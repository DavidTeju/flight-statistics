#!/usr/bin/env python3
"""One-off cleanup for the "TSA Total Throughput" header-poisoning bug.

The parser used to set carry.iata before validating the row was a data row,
so page headers like "TSA Total Throughput" leaked 'TSA' into subsequent rows
as the airport IATA. Parser is fixed; this script:

  1. Lists every PDF whose ingest produced an iata='TSA' row.
  2. Re-parses each affected PDF with the fixed parser, UPSERTing rows into
     tsa_hourly (corrects the leaked rows in place).
  3. Drops the bogus airport row and its now-orphan checkpoints/hourly rows.
"""
from __future__ import annotations
import sqlite3, subprocess, sys, csv as _csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'flight_stats.sqlite'
PARSER = ROOT / 'parse_tsa_pdf.py'
VENV_PY = ROOT / '.venv' / 'bin' / 'python'
CACHE = ROOT / 'cache' / 'tsa-foia'


def affected_pdfs(conn):
    """PDFs whose ingest produced an iata='TSA' header-poisoning row."""
    return [row[0] for row in conn.execute('''
        SELECT DISTINCT ir.source_filename
        FROM   ingest_run ir
        JOIN   tsa_hourly h ON h.ingest_run_id = ir.id
        JOIN   checkpoint c ON c.id = h.checkpoint_id
        WHERE  c.airport_iata = 'TSA'
        ORDER BY ir.source_filename
    ''')]


def zero_row_pdfs(conn):
    """PDFs whose latest ingest_run produced zero rows — likely PMIS failures
    the old parser dropped silently."""
    return [row[0] for row in conn.execute('''
        SELECT source_filename
        FROM   ingest_run
        WHERE  source='tsa_foia' AND row_count=0
          AND  source_filename IS NOT NULL
        ORDER BY source_filename
    ''')]


def upsert_airport(conn, iata, name, city, state):
    conn.execute('''INSERT INTO airport(iata,name,city,state)
                    VALUES (?,?,?,?)
                    ON CONFLICT(iata) DO UPDATE SET
                      name=COALESCE(NULLIF(excluded.name,''), airport.name),
                      city=COALESCE(NULLIF(excluded.city,''), airport.city),
                      state=COALESCE(NULLIF(excluded.state,''), airport.state)''',
                 (iata, name, city, state))


def upsert_checkpoint(conn, iata, name, cache):
    key = (iata, name)
    if key in cache:
        return cache[key]
    cur = conn.execute('SELECT id FROM checkpoint WHERE airport_iata=? AND name=?', (iata, name))
    row = cur.fetchone()
    if row:
        cache[key] = row[0]
        return row[0]
    cur = conn.execute('INSERT INTO checkpoint(airport_iata,name) VALUES (?,?)', (iata, name))
    cache[key] = cur.lastrowid
    return cache[key]


def parse_subprocess(pdf_name: str) -> tuple[str, list[tuple] | Exception]:
    """Run the parser subprocess and return the parsed rows.

    Pure CPU work in another process, so a ThreadPoolExecutor here gives real
    parallelism. DB inserts stay in the main thread (SQLite serializes writes).
    """
    pdf = CACHE / pdf_name
    if not pdf.exists():
        return pdf_name, FileNotFoundError(str(pdf))
    try:
        proc = subprocess.run(
            [str(VENV_PY), '-u', str(PARSER), str(pdf), '-o', '-'],
            capture_output=True, text=True, check=True, timeout=900
        )
    except subprocess.CalledProcessError as e:
        return pdf_name, e
    rows = []
    reader = _csv.reader(proc.stdout.splitlines())
    next(reader, None)
    for r in reader:
        if len(r) != 8:
            continue
        date, hour, iata, name, city, state, cp, pax = r
        try:
            hour = int(hour); pax = int(pax)
        except ValueError:
            continue
        rows.append((date, hour, iata, name, city, state, cp, pax))
    return pdf_name, rows


def insert_rows(conn, rows, run_id):
    ck_cache = {}
    apt_seen = set()
    for date, hour, iata, name, city, state, cp, pax in rows:
        if iata not in apt_seen:
            upsert_airport(conn, iata, name, city, state)
            apt_seen.add(iata)
        cid = upsert_checkpoint(conn, iata, cp, ck_cache)
        conn.execute('''INSERT INTO tsa_hourly(date, hour, checkpoint_id, pax_incl_kcm, ingest_run_id)
                        VALUES (?,?,?,?,?)
                        ON CONFLICT(date, hour, checkpoint_id) DO UPDATE SET
                          pax_incl_kcm=excluded.pax_incl_kcm,
                          ingest_run_id=excluded.ingest_run_id''',
                     (date, hour, cid, pax, run_id))
    return len(rows)


def main():
    conn = sqlite3.connect(str(DB))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')

    tsa_pdfs = affected_pdfs(conn)
    zero_pdfs = zero_row_pdfs(conn)
    # Dedupe while preserving order
    seen = set()
    pdfs = []
    for p in tsa_pdfs + zero_pdfs:
        if p not in seen:
            seen.add(p)
            pdfs.append(p)
    print(f'{len(tsa_pdfs)} TSA-bug PDFs + {len(zero_pdfs)} zero-row PDFs = {len(pdfs)} to reparse', file=sys.stderr)

    total = 0
    done = 0
    # 4 parallel parser subprocesses; DB inserts stay serial in the main thread.
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(parse_subprocess, p): p for p in pdfs}
        for fut in as_completed(futs):
            pdf_name, result = fut.result()
            done += 1
            if isinstance(result, Exception):
                print(f'  [{done}/{len(pdfs)}] FAIL {pdf_name}: {result!r}', file=sys.stderr, flush=True)
                continue
            cur = conn.execute('''INSERT INTO ingest_run(source, fetched_at, source_url, source_filename, row_count, covers_from, covers_to, notes)
                                  VALUES ('tsa_foia', datetime('now'), '<reparsed>', ?, 0, '', '', 'tsa-bug reparse')''',
                               (pdf_name,))
            run_id = cur.lastrowid
            with conn:
                n = insert_rows(conn, result, run_id)
            conn.execute('UPDATE ingest_run SET row_count=? WHERE id=?', (n, run_id))
            conn.commit()
            total += n
            print(f'  [{done}/{len(pdfs)}] {pdf_name}: +{n:,}', file=sys.stderr, flush=True)

    # Now drop the bogus iata='TSA' airport and its dependents
    print('\ndeleting orphan TSA rows…', file=sys.stderr, flush=True)
    n_hourly = conn.execute('''DELETE FROM tsa_hourly WHERE checkpoint_id IN
                               (SELECT id FROM checkpoint WHERE airport_iata='TSA')''').rowcount
    n_ck = conn.execute("DELETE FROM checkpoint WHERE airport_iata='TSA'").rowcount
    n_apt = conn.execute("DELETE FROM airport WHERE iata='TSA'").rowcount
    conn.commit()
    print(f'  deleted: {n_hourly} hourly, {n_ck} checkpoints, {n_apt} airport row(s)', file=sys.stderr)
    print(f'\nreparsed total rows: {total:,}', file=sys.stderr)


if __name__ == '__main__':
    main()
