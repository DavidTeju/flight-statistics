#!/usr/bin/env python3
"""Download all archived TSA FOIA throughput PDFs from the Wayback Machine,
parse each, and insert rows into the SQLite database.

Usage:
    python3 db/ingest_tsa_foia.py [--limit N] [--from YYYY-MM-DD]

Concurrency: downloads happen in a thread pool; PDF→rows parsing happens
sequentially (CPU-bound, single-threaded pdftotext + Python). DB inserts
happen in batched transactions.
"""
from __future__ import annotations
import argparse, json, os, sqlite3, subprocess, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import urllib.request

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'flight_stats.sqlite'
CACHE = ROOT / 'cache' / 'tsa-foia'
URLS_JSON = Path('/tmp/foia_all_urls.json')

WB_TEMPLATE = 'https://web.archive.org/web/{ts}id_/{url}'

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'


def wb_url(timestamp: str, original: str) -> str:
    # '0' tells Wayback to redirect to the closest snapshot, no exact ts needed.
    return WB_TEMPLATE.format(ts=timestamp or '0', url=original)


def safe_filename(url: str) -> str:
    return urllib.parse.unquote(url.split('/')[-1]).replace('/', '_')


def fetch_one(entry: dict, retries: int = 4) -> Path | None:
    """Download a PDF from the live TSA site first, falling back to Wayback."""
    fn = safe_filename(entry['orig'])
    out = CACHE / fn
    if out.exists() and out.stat().st_size > 100_000:
        return out
    tmp = out.with_suffix('.pdf.part')
    candidates = [entry['orig'], wb_url(entry.get('ts', ''), entry['orig'])]
    last_err = None
    for url in candidates:
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=120) as r:
                    if r.status != 200:
                        last_err = f'HTTP {r.status}'
                        continue
                    data = r.read()
                if not data.startswith(b'%PDF'):
                    last_err = f'not a pdf (first bytes: {data[:8]!r})'
                    continue
                tmp.write_bytes(data)
                tmp.rename(out)
                return out
            except Exception as e:
                last_err = repr(e)
                time.sleep(1 + attempt * 2)
    print(f'  FAIL: {fn}: {last_err}', file=sys.stderr, flush=True)
    return None


def ensure_indexes(conn):
    conn.execute('CREATE INDEX IF NOT EXISTS _airport_iata_idx ON airport(iata)')


def upsert_airport(conn, iata, name, city, state):
    conn.execute('''INSERT INTO airport(iata,name,city,state)
                    VALUES (?,?,?,?)
                    ON CONFLICT(iata) DO UPDATE SET
                      name=COALESCE(NULLIF(excluded.name,''), airport.name),
                      city=COALESCE(NULLIF(excluded.city,''), airport.city),
                      state=COALESCE(NULLIF(excluded.state,''), airport.state)''',
                 (iata, name, city, state))


def upsert_checkpoint(conn, iata, name) -> int:
    cur = conn.execute('SELECT id FROM checkpoint WHERE airport_iata=? AND name=?', (iata, name))
    row = cur.fetchone()
    if row: return row[0]
    cur = conn.execute('INSERT INTO checkpoint(airport_iata,name) VALUES (?,?)', (iata, name))
    return cur.lastrowid


def parse_pdf_subprocess(pdf_path: Path) -> list[tuple]:
    """Run parser as a subprocess so pdfplumber memory is released between PDFs."""
    parser = Path(__file__).parent / 'parse_tsa_pdf.py'
    venv_py = Path(__file__).parent / '.venv' / 'bin' / 'python'
    py = str(venv_py) if venv_py.exists() else 'python3'
    proc = subprocess.run(
        [py, '-u', str(parser), str(pdf_path), '-o', '-'],
        capture_output=True, text=True, check=True, timeout=600
    )
    import csv as _csv
    rows = []
    reader = _csv.reader(proc.stdout.splitlines())
    header = next(reader, None)
    for r in reader:
        if len(r) != 8:
            continue
        date, hour, iata, name, city, state, cp, pax = r
        try:
            rows.append((date, int(hour), iata, name, city, state, cp, int(pax)))
        except ValueError:
            continue
    return rows


def ingest_pdf(conn, pdf_path: Path, run_id: int) -> tuple[int, str, str]:
    rows = parse_pdf_subprocess(pdf_path)
    if not rows:
        return (0, '', '')

    # Cache lookups for speed
    ck_cache: dict[tuple[str, str], int] = {}
    apt_seen: set[str] = set()
    dates_seen: set[str] = set()

    with conn:
        for date, hour, iata, name, city, state, cp_name, pax in rows:
            if iata not in apt_seen:
                upsert_airport(conn, iata, name, city, state)
                apt_seen.add(iata)
            key = (iata, cp_name)
            cid = ck_cache.get(key)
            if cid is None:
                cid = upsert_checkpoint(conn, iata, cp_name)
                ck_cache[key] = cid
            conn.execute('''INSERT INTO tsa_hourly(date, hour, checkpoint_id, pax_incl_kcm, ingest_run_id)
                            VALUES (?,?,?,?,?)
                            ON CONFLICT(date, hour, checkpoint_id) DO UPDATE SET
                              pax_incl_kcm=excluded.pax_incl_kcm,
                              ingest_run_id=excluded.ingest_run_id''',
                         (date, hour, cid, pax, run_id))
            dates_seen.add(date)

    return (len(rows), min(dates_seen), max(dates_seen))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--from', dest='from_date', default='2019-01-01')
    ap.add_argument('--to', dest='to_date', default='2099-12-31')
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()

    urls = json.loads(URLS_JSON.read_text())
    urls = [u for u in urls if args.from_date <= u['from'] <= args.to_date]
    urls.sort(key=lambda u: u['from'])
    if args.limit:
        urls = urls[:args.limit]
    print(f'queued {len(urls)} PDFs ({urls[0]["from"]} → {urls[-1]["from"]})', file=sys.stderr, flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')

    # Download phase (parallel)
    paths = [None] * len(urls)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, u): i for i, u in enumerate(urls)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            paths[i] = fut.result()
            done += 1
            if done % 5 == 0 or done == len(urls):
                ok = sum(1 for p in paths if p)
                print(f'  download {done}/{len(urls)} (ok={ok})', file=sys.stderr, flush=True)

    # Parse + ingest phase (sequential).
    # Skip any PDF whose covers_from already has tsa_hourly rows.
    existing_dates = {r[0] for r in conn.execute('SELECT DISTINCT date FROM tsa_hourly')}
    total_rows = 0
    for i, (u, p) in enumerate(zip(urls, paths)):
        if p is None:
            continue
        if u['from'] in existing_dates:
            # Already ingested in a prior run
            print(f'  skip {p.name} (already ingested)', file=sys.stderr, flush=True)
            continue
        cur = conn.execute('''INSERT INTO ingest_run(source,fetched_at,source_url,source_filename,row_count,covers_from,covers_to,notes)
                              VALUES ('tsa_foia', datetime('now'), ?, ?, 0, ?, ?, NULL)''',
                           (u['orig'], p.name, u['from'], u['to']))
        run_id = cur.lastrowid
        try:
            n, dmin, dmax = ingest_pdf(conn, p, run_id)
        except Exception as e:
            print(f'  PARSE FAIL {p.name}: {e}', file=sys.stderr, flush=True)
            continue
        conn.execute('UPDATE ingest_run SET row_count=?, covers_from=?, covers_to=? WHERE id=?',
                     (n, dmin or u['from'], dmax or u['to'], run_id))
        conn.commit()
        total_rows += n
        if (i+1) % 5 == 0 or i+1 == len(urls):
            print(f'  ingest {i+1}/{len(urls)} • +{n:>6} rows • {p.name}', file=sys.stderr, flush=True)

    print(f'\ndone. total rows inserted: {total_rows}', file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()
