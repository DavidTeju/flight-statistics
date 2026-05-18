#!/usr/bin/env python3
"""Parse a TSA weekly throughput PDF → CSV rows of
(date, hour, airport_iata, airport_name, city, state, checkpoint, pax_incl_kcm).

Two PDF formats need different strategies:

  * 2022-present "TSA Total Throughput" — clean columnar layout with
    "Total Pax + KCM PAX" header. `pdftotext -layout` preserves columns
    perfectly. Fast (~5–15 s/PDF) and low-memory.

  * 2019-2021 "TSA Throughput" — multi-line cells (wrapped dates, names) and
    a "PMIS - Total Customer Throughput" header. Column slicing fails on the
    wraps; pdfplumber's table extraction handles it but is slow (~3–6 min/PDF)
    and memory-hungry.

We detect the format from the first page's text and dispatch to the right
parser. Both paths stream rows to a writer rather than accumulating, and the
pdfplumber path flushes each page's cache + forces GC every N pages to keep
RSS bounded.
"""
from __future__ import annotations
import argparse, csv, gc, re, subprocess, sys
from pathlib import Path


# ─── shared helpers ─────────────────────────────────────────────────────

_DATE_RE = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
_HOUR_RE = re.compile(r'(\d{1,2}):(\d{2})')
_IATA_RE = re.compile(r'^[A-Z0-9]{3}$')
_PAX_RE  = re.compile(r'(-?\d[\d,]*)')


def _norm(cell):
    if cell is None:
        return ''
    return ' '.join(cell.replace('\n', ' ').split())


def _parse_date(cell):
    cell = (cell or '').replace('\n', '').replace(' ', '')
    m = _DATE_RE.match(cell)
    if not m:
        return None
    mm, dd, yyyy = int(m[1]), int(m[2]), int(m[3])
    return f'{yyyy:04d}-{mm:02d}-{dd:02d}'


def _parse_hour(cell):
    cell = (cell or '').replace('\n', '').strip()
    m = _HOUR_RE.match(cell)
    return int(m[1]) if m else None


def _parse_pax(cell):
    cell = (cell or '').replace(',', '').replace('\n', ' ').strip()
    m = _PAX_RE.search(cell)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


class Carry:
    __slots__ = ('date', 'hour', 'iata', 'apt', 'city', 'state')
    def __init__(self):
        self.date = self.hour = self.iata = None
        self.apt = self.city = self.state = None


# ─── fast path: pdftotext + column slicing (2022+ KCM format) ───────────

def _find_cols_kcm(lines):
    """Find header columns in the new "TSA Total Throughput" PDFs.

    Header line example:
        Date       of      Airport ...         City        State   Checkpoint
    """
    for ln in lines:
        if 'Date' in ln and 'Airport' in ln and 'City' in ln and 'State' in ln and 'Checkpoint' in ln:
            return {
                'date': ln.find('Date'),
                'hour': ln.find('Hour') if 'Hour' in ln else 11,
                'airport': ln.find('Airport'),
                'city': ln.find('City'),
                'state': ln.find('State'),
                'checkpoint': ln.find('Checkpoint'),
            }
    return None


_DATE_LINE_RE = re.compile(r'^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$')
_HOUR_LINE_RE = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*$')
_PAX_LINE_RE  = re.compile(r'(-?\d[\d,]*)\s*$')
_IATA_LINE_RE = re.compile(r'^([A-Z0-9]{3})\b')


def _parse_kcm(pdf_path: str, writer) -> int:
    raw = subprocess.run(
        ['pdftotext', '-layout', str(pdf_path), '-'],
        check=True, capture_output=True, text=True
    ).stdout
    pages = raw.split('\f')
    cols = None
    carry = Carry()
    total = 0
    for page in pages:
        page_lines = page.splitlines()
        page_cols = _find_cols_kcm(page_lines)
        if page_cols:
            cols = page_cols
        if cols is None:
            continue
        for ln in page_lines:
            if not ln.strip():
                continue
            # Validate this line is a data row BEFORE updating any carries.
            # Title rows like "TSA Total Throughput" centered on a page slice
            # into the airport column and the literal "TSA" matches the IATA
            # regex — a silent carry-forward poison if accepted.
            rest = ln[cols['checkpoint']:]
            if not rest.strip():
                continue
            mp = _PAX_LINE_RE.search(rest)
            if not mp:
                continue
            cp = rest[:mp.start()].rstrip()
            if not cp or cp.lower().startswith('checkpoint'):
                continue
            try:
                pax = int(mp.group(1).replace(',', ''))
            except ValueError:
                continue

            d_cell = ln[cols['date']:cols['hour']].strip()
            m = _DATE_LINE_RE.match(d_cell)
            if m:
                mm, dd, yyyy = int(m[1]), int(m[2]), int(m[3])
                carry.date = f'{yyyy:04d}-{mm:02d}-{dd:02d}'

            h_cell = ln[cols['hour']:cols['airport']].strip()
            m = _HOUR_LINE_RE.match(h_cell)
            if m:
                carry.hour = int(m[1])

            a_cell = ln[cols['airport']:cols['city']].strip()
            if a_cell:
                mi = _IATA_LINE_RE.match(a_cell)
                if mi:
                    carry.iata = mi.group(1)
                    rest_name = a_cell[3:].strip()
                    if rest_name:
                        carry.apt = rest_name

            c_cell = ln[cols['city']:cols['state']].strip()
            if c_cell and not c_cell.lower().startswith('city'):
                carry.city = c_cell

            s_cell = ln[cols['state']:cols['checkpoint']].strip()
            if re.fullmatch(r'[A-Z]{2}', s_cell):
                carry.state = s_cell

            if carry.date is None or carry.hour is None or carry.iata is None:
                continue
            writer.writerow((
                carry.date, carry.hour, carry.iata, carry.apt or '',
                carry.city or '', carry.state or '', cp, pax,
            ))
            total += 1
    return total


# ─── slow path: pdfplumber (2019-2021 PMIS format) ──────────────────────

PAGES_PER_GC = 25


def _find_table_cols(header_row):
    out = {}
    for i, raw in enumerate(header_row):
        h = _norm(raw).lower()
        if 'date' in h and 'date' not in out:                    out['date'] = i
        elif 'hour' in h and 'hour' not in out:                  out['hour'] = i
        elif 'airport' in h and 'airport' not in out:            out['airport'] = i
        elif h == 'city' or h.startswith('city'):                out['city'] = i
        elif h == 'state' or h.startswith('state'):              out['state'] = i
        elif h.startswith('checkpoint') and 'checkpoint' not in out: out['checkpoint'] = i
        elif ('pax' in h or 'throughput' in h or 'kcm' in h) and 'pax' not in out:
            out['pax'] = i
    return out


def _process_table(table, cols, carry, writer):
    n = 0
    for row in table:
        if not any(cell for cell in row):
            continue

        # Validate this is a data row BEFORE updating carries — see KCM path
        # comment about "TSA Total Throughput" poisoning the iata carry.
        cp = _norm(row[cols['checkpoint']]) if cols['checkpoint'] < len(row) else ''
        if not cp or cp.lower().startswith('checkpoint'):
            continue
        pax = _parse_pax(row[cols['pax']]) if cols['pax'] < len(row) else None
        if pax is None:
            continue

        if 'date' in cols and cols['date'] < len(row):
            d = _parse_date(row[cols['date']])
            if d:
                carry.date = d

        if 'hour' in cols and cols['hour'] < len(row):
            h = _parse_hour(row[cols['hour']])
            if h is not None:
                carry.hour = h

        if cols['airport'] < len(row):
            a_cell = _norm(row[cols['airport']])
            if a_cell and _IATA_RE.match(a_cell.split(' ', 1)[0]):
                iata, _, rest = a_cell.partition(' ')
                carry.iata = iata
                carry.apt = rest.strip() or carry.apt

        if 'city' in cols and cols['airport'] + 1 < cols['city']:
            idx = cols['airport'] + 1
            name_cell = _norm(row[idx]) if idx < len(row) else ''
            if name_cell and name_cell != carry.apt:
                if not any(s in name_cell.lower() for s in (', ', ' ak', ' ca')):
                    carry.apt = name_cell

        if 'city' in cols and cols['city'] < len(row):
            c = _norm(row[cols['city']]).rstrip(',')
            if c and not c.lower().startswith('city'):
                carry.city = c

        if 'state' in cols and cols['state'] < len(row):
            s = _norm(row[cols['state']])
            if re.fullmatch(r'[A-Z]{2}', s):
                carry.state = s

        if carry.date is None or carry.hour is None or carry.iata is None:
            continue

        writer.writerow((
            carry.date, carry.hour, carry.iata, carry.apt or '',
            carry.city or '', carry.state or '', cp, pax,
        ))
        n += 1
    return n


def _parse_pmis(pdf_path: str, writer) -> int:
    import pdfplumber
    carry = Carry()
    cols = None
    total = 0
    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables() or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    new_cols = _find_table_cols(table[0])
                    if 'pax' in new_cols and 'airport' in new_cols and 'checkpoint' in new_cols:
                        cols = new_cols
                        total += _process_table(table[1:], cols, carry, writer)
                    elif cols is not None:
                        total += _process_table(table, cols, carry, writer)
            finally:
                try: page.flush_cache()
                except Exception: pass
                try: page.close()
                except Exception: pass
            if pi % PAGES_PER_GC == PAGES_PER_GC - 1:
                gc.collect()
    return total


# ─── format dispatch ────────────────────────────────────────────────────

def _detect_format(pdf_path: str) -> str:
    """Return 'kcm' or 'pmis' based on first-page text."""
    out = subprocess.run(
        ['pdftotext', '-layout', '-f', '1', '-l', '1', str(pdf_path), '-'],
        check=True, capture_output=True, text=True
    ).stdout
    if 'KCM' in out or 'Total Pax' in out:
        return 'kcm'
    if 'PMIS' in out or 'Customer' in out:
        return 'pmis'
    # Default to slower-but-safer pdfplumber path
    return 'pmis'


def parse_pdf_streaming(pdf_path: str, writer) -> int:
    fmt = _detect_format(pdf_path)
    if fmt == 'kcm':
        return _parse_kcm(pdf_path, writer)
    return _parse_pmis(pdf_path, writer)


# Back-compat shim: callers that import parse_pdf get a list.
def parse_pdf(pdf_path: str):
    rows = []
    class _ListWriter:
        def writerow(self, r): rows.append(tuple(r))
    parse_pdf_streaming(pdf_path, _ListWriter())
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdfs', nargs='+')
    ap.add_argument('-o', '--out', default='-')
    args = ap.parse_args()
    out_f = sys.stdout if args.out == '-' else open(args.out, 'w', newline='')
    w = csv.writer(out_f)
    w.writerow(['date','hour','airport_iata','airport_name','city','state','checkpoint','pax_incl_kcm'])
    for path in args.pdfs:
        n = parse_pdf_streaming(path, w)
        out_f.flush()
        print(f'{path}: {n} rows', file=sys.stderr, flush=True)
    if out_f is not sys.stdout:
        out_f.close()


if __name__ == '__main__':
    main()
