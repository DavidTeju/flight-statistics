#!/usr/bin/env python3
"""Build derived rollup tables from the raw fact tables.

  tsa_daily_by_airport          ← sum tsa_hourly across hours+checkpoints
  enplanements_monthly_by_airport ← sum t100_segment origins by passenger class
  airport_pax_daily             ← unified daily fact (TSA + enplanements)

Run after each refresh of either raw source. Idempotent — wipes its targets.
"""
from __future__ import annotations
import calendar, sqlite3, sys
from pathlib import Path

DB = Path(__file__).resolve().parent / 'flight_stats.sqlite'

# T-100 service classes that count as passenger-carrying scheduled service.
# F = Scheduled Passenger, L = Non-scheduled (passenger), G = all-cargo (skip).
PASSENGER_CLASSES = ('F', 'L', 'A', 'C', 'E', 'P')


def main():
    conn = sqlite3.connect(str(DB))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')

    print('rebuild tsa_daily_by_airport …', file=sys.stderr)
    conn.execute('DELETE FROM tsa_daily_by_airport')
    conn.execute('''
        INSERT INTO tsa_daily_by_airport(date, airport_iata, pax_incl_kcm)
        SELECT h.date, c.airport_iata, SUM(h.pax_incl_kcm)
        FROM   tsa_hourly h JOIN checkpoint c ON c.id = h.checkpoint_id
        GROUP BY h.date, c.airport_iata
    ''')
    n1 = conn.execute('SELECT COUNT(*) FROM tsa_daily_by_airport').fetchone()[0]
    print(f'  {n1:,} rows', file=sys.stderr)

    print('rebuild enplanements_monthly_by_airport …', file=sys.stderr)
    conn.execute('DELETE FROM enplanements_monthly_by_airport')
    conn.execute(f'''
        INSERT INTO enplanements_monthly_by_airport(year, month, airport_iata, passengers)
        SELECT year, month, origin_iata, SUM(passengers)
        FROM   t100_segment
        WHERE  service_class IN ({','.join('?'*len(PASSENGER_CLASSES))})
          AND  aircraft_config = 1                  -- passenger config only
        GROUP BY year, month, origin_iata
    ''', PASSENGER_CLASSES)
    n2 = conn.execute('SELECT COUNT(*) FROM enplanements_monthly_by_airport').fetchone()[0]
    print(f'  {n2:,} rows', file=sys.stderr)

    print('rebuild airport_pax_daily …', file=sys.stderr)
    conn.execute('DELETE FROM airport_pax_daily')

    # 1) TSA per-airport daily (granularity=day)
    conn.execute('''
        INSERT INTO airport_pax_daily(date, airport_iata, metric, passengers, source, granularity, is_estimated)
        SELECT date, airport_iata, 'tsa_throughput', pax_incl_kcm,
               'tsa_foia', 'day', 0
        FROM   tsa_daily_by_airport
    ''')

    # 2) TSA national daily — virtual airport '__US__'
    conn.execute('''
        INSERT INTO airport_pax_daily(date, airport_iata, metric, passengers, source, granularity, is_estimated)
        SELECT date, '__US__', 'tsa_throughput', pax_incl_kcm,
               source, 'day', 0
        FROM   tsa_daily_national
    ''')

    # 3) Enplanements monthly → apportion uniformly across days in the month
    #    (granularity=month_apportioned, is_estimated=1).
    cur = conn.execute('''
        SELECT year, month, airport_iata, passengers
        FROM   enplanements_monthly_by_airport
    ''')
    batch = []
    for year, month, iata, pax in cur:
        days = calendar.monthrange(year, month)[1]
        per_day = pax // days
        remainder = pax - per_day * days
        for d in range(1, days + 1):
            date = f'{year:04d}-{month:02d}-{d:02d}'
            # Spread the remainder across the first `remainder` days
            value = per_day + (1 if d <= remainder else 0)
            batch.append((date, iata, 'enplanements_domestic', value, 'bts_t100', 'month_apportioned', 1))
    conn.executemany('''
        INSERT INTO airport_pax_daily(date, airport_iata, metric, passengers, source, granularity, is_estimated)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(date, airport_iata, metric) DO UPDATE SET
          passengers = excluded.passengers,
          source = excluded.source,
          granularity = excluded.granularity,
          is_estimated = excluded.is_estimated
    ''', batch)

    n3 = conn.execute('SELECT COUNT(*) FROM airport_pax_daily').fetchone()[0]
    print(f'  {n3:,} rows', file=sys.stderr)
    conn.commit()

    # Summary
    print('\nsummary:', file=sys.stderr)
    for q in [
        ("tsa_hourly",                  'SELECT COUNT(*), MIN(date), MAX(date) FROM tsa_hourly'),
        ("tsa_daily_by_airport",        'SELECT COUNT(*), MIN(date), MAX(date) FROM tsa_daily_by_airport'),
        ("tsa_daily_national",          'SELECT COUNT(*), MIN(date), MAX(date) FROM tsa_daily_national'),
        ("t100_segment",                'SELECT COUNT(*), MIN(year), MAX(year) FROM t100_segment'),
        ("enplanements_monthly_by_airport", 'SELECT COUNT(*), MIN(year), MAX(year) FROM enplanements_monthly_by_airport'),
        ("airport_pax_daily",           'SELECT COUNT(*), MIN(date), MAX(date) FROM airport_pax_daily'),
        ("airport",                     'SELECT COUNT(*) FROM airport'),
        ("checkpoint",                  'SELECT COUNT(*) FROM checkpoint'),
        ("carrier",                     'SELECT COUNT(*) FROM carrier'),
    ]:
        name, sql = q
        r = conn.execute(sql).fetchone()
        print(f'  {name:35} {r}', file=sys.stderr)


if __name__ == '__main__':
    main()
