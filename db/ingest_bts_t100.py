#!/usr/bin/env python3
"""Ingest BTS T-100 segment CSV zips into the SQLite database.

Each year-zip is parsed and inserted into t100_segment. Airport + carrier
dimension rows are upserted on the fly from the same data.

Usage:  python3 db/ingest_bts_t100.py
"""
from __future__ import annotations
import csv, sqlite3, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'flight_stats.sqlite'
CACHE = ROOT / 'cache' / 'bts-t100'


# CSV columns we map → t100_segment columns
CSV_TO_DB = {
    'YEAR': 'year',
    'MONTH': 'month',
    'UNIQUE_CARRIER': 'unique_carrier',
    'REGION': 'carrier_region',
    'ORIGIN': 'origin_iata',
    'ORIGIN_AIRPORT_ID': 'origin_airport_id',
    'ORIGIN_AIRPORT_SEQ_ID': 'origin_airport_seq_id',
    'DEST': 'dest_iata',
    'DEST_AIRPORT_ID': 'dest_airport_id',
    'DEST_AIRPORT_SEQ_ID': 'dest_airport_seq_id',
    'AIRCRAFT_GROUP': 'aircraft_group',
    'AIRCRAFT_TYPE': 'aircraft_type',
    'AIRCRAFT_CONFIG': 'aircraft_config',
    'CLASS': 'service_class',
    'PASSENGERS': 'passengers',
    'SEATS': 'seats',
    'DEPARTURES_SCHEDULED': 'dep_scheduled',
    'DEPARTURES_PERFORMED': 'dep_performed',
    'FREIGHT': 'freight_lb',
    'MAIL': 'mail_lb',
    'DISTANCE': 'distance_mi',
    'AIR_TIME': 'air_time_min',
    'RAMP_TO_RAMP': 'ramp_time_min',
}


def to_int(v: str) -> int:
    if v in ('', None):
        return 0
    try:
        return int(float(v))
    except ValueError:
        return 0


def ingest_zip(conn: sqlite3.Connection, zip_path: Path, run_id: int) -> int:
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = next(n for n in zf.namelist() if n.upper().endswith('.CSV') and 'DOCUMENTATION' not in n.upper())
        with zf.open(csv_name) as f:
            text = (l.decode('latin-1') for l in f)
            reader = csv.DictReader(text)

            carriers_seen: set[str] = set()
            airports_seen: set[str] = set()
            batch: list[tuple] = []
            n = 0

            def flush():
                if not batch: return
                conn.executemany('''INSERT INTO t100_segment(
                    year, month, unique_carrier, carrier_region,
                    origin_iata, origin_airport_id, origin_airport_seq_id,
                    dest_iata, dest_airport_id, dest_airport_seq_id,
                    aircraft_group, aircraft_type, aircraft_config, service_class,
                    passengers, seats, dep_scheduled, dep_performed,
                    freight_lb, mail_lb, distance_mi, air_time_min, ramp_time_min,
                    ingest_run_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', batch)
                batch.clear()

            for row in reader:
                # Upsert carrier
                uc = row['UNIQUE_CARRIER']
                if uc and uc not in carriers_seen:
                    conn.execute('''INSERT INTO carrier(unique_carrier, airline_id, iata_carrier, name)
                                    VALUES (?,?,?,?)
                                    ON CONFLICT(unique_carrier) DO UPDATE SET
                                      airline_id=excluded.airline_id,
                                      iata_carrier=COALESCE(NULLIF(excluded.iata_carrier,''), carrier.iata_carrier),
                                      name=COALESCE(NULLIF(excluded.name,''), carrier.name)''',
                                 (uc, to_int(row['AIRLINE_ID']), row.get('CARRIER') or None,
                                  row['UNIQUE_CARRIER_NAME'] or uc))
                    carriers_seen.add(uc)

                # Upsert origin airport
                for prefix in ('ORIGIN', 'DEST'):
                    iata = row[prefix]
                    if not iata or iata in airports_seen:
                        continue
                    apt_id = to_int(row[f'{prefix}_AIRPORT_ID'])
                    conn.execute('''INSERT INTO airport(iata, dot_airport_id, name, city, state,
                                                          state_fips, city_market_id, wac)
                                    VALUES (?,?,?,?,?,?,?,?)
                                    ON CONFLICT(iata) DO UPDATE SET
                                      dot_airport_id=COALESCE(airport.dot_airport_id, excluded.dot_airport_id),
                                      city=COALESCE(NULLIF(excluded.city,''), airport.city),
                                      state=COALESCE(NULLIF(excluded.state,''), airport.state),
                                      state_fips=COALESCE(NULLIF(excluded.state_fips,''), airport.state_fips),
                                      city_market_id=COALESCE(excluded.city_market_id, airport.city_market_id),
                                      wac=COALESCE(excluded.wac, airport.wac)''',
                                 (
                                    iata,
                                    apt_id or None,
                                    row[f'{prefix}_CITY_NAME'] or iata,
                                    row[f'{prefix}_CITY_NAME'].split(',')[0] if row[f'{prefix}_CITY_NAME'] else '',
                                    row[f'{prefix}_STATE_ABR'] or '',
                                    row[f'{prefix}_STATE_FIPS'] or None,
                                    to_int(row[f'{prefix}_CITY_MARKET_ID']) or None,
                                    to_int(row[f'{prefix}_WAC']) or None,
                                 ))
                    airports_seen.add(iata)

                batch.append((
                    to_int(row['YEAR']), to_int(row['MONTH']),
                    uc, row['REGION'] or '',
                    row['ORIGIN'], to_int(row['ORIGIN_AIRPORT_ID']), to_int(row['ORIGIN_AIRPORT_SEQ_ID']),
                    row['DEST'], to_int(row['DEST_AIRPORT_ID']), to_int(row['DEST_AIRPORT_SEQ_ID']),
                    to_int(row['AIRCRAFT_GROUP']), to_int(row['AIRCRAFT_TYPE']), to_int(row['AIRCRAFT_CONFIG']),
                    row['CLASS'] or '',
                    to_int(row['PASSENGERS']), to_int(row['SEATS']),
                    to_int(row['DEPARTURES_SCHEDULED']), to_int(row['DEPARTURES_PERFORMED']),
                    to_int(row['FREIGHT']), to_int(row['MAIL']),
                    to_int(row['DISTANCE']), to_int(row['AIR_TIME']), to_int(row['RAMP_TO_RAMP']),
                    run_id,
                ))
                n += 1
                if len(batch) >= 5000:
                    flush()

            flush()
            return n


def main():
    conn = sqlite3.connect(str(DB))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')

    total = 0
    zips = sorted(CACHE.glob('t100_domestic_*.zip'))
    for zp in zips:
        year = zp.stem.rsplit('_', 1)[-1]

        cur = conn.execute('''INSERT INTO ingest_run(source, fetched_at, source_url, source_filename, row_count, covers_from, covers_to, notes)
                              VALUES ('bts_t100_domestic', datetime('now'), 'https://transtats.bts.gov/DL_SelectFields.aspx', ?, 0, ?, ?, NULL)''',
                           (zp.name, f'{year}-01-01', f'{year}-12-31'))
        run_id = cur.lastrowid

        with conn:
            try:
                n = ingest_zip(conn, zp, run_id)
            except Exception as e:
                print(f'  FAIL {zp.name}: {e}', file=sys.stderr)
                continue

        conn.execute('UPDATE ingest_run SET row_count=? WHERE id=?', (n, run_id))
        conn.commit()
        total += n
        print(f'  {zp.name}: +{n:,} rows', file=sys.stderr)

    print(f'\ndone. total rows: {total:,}', file=sys.stderr)


if __name__ == '__main__':
    main()
