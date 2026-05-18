# Flight Statistics — Data Warehouse

SQLite database (`flight_stats.sqlite`) seeded from two upstream sources:

| Source                                                                                | Coverage                                                     | Grain                |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------- |
| **TSA public passenger-volumes page**                                                 | 2019-01-01 → present (daily, national)                       | `tsa_daily_national` |
| **TSA FOIA weekly throughput PDFs** (via Wayback Machine + tsa.gov FOIA reading room) | 2019-01-20 → present (weekly batches, hourly per-checkpoint) | `tsa_hourly`         |
| **BTS T-100 Domestic Segment, U.S. Carriers** (TranStats download form)               | 2019-01 → 2026-02 (monthly, carrier × O/D × aircraft)        | `t100_segment`       |

## Layout

```
db/
├── schema.sql              canonical DDL — sqlite-flavored, mostly portable
├── flight_stats.sqlite     the database itself
├── parse_tsa_pdf.py        TSA weekly PDF → rows (uses pdfplumber)
├── ingest_tsa_foia.py      download + parse + load TSA FOIA PDFs
├── download_bts_t100.mjs   Playwright-driven download of BTS T-100 zips
├── ingest_bts_t100.py      load downloaded T-100 zips into t100_segment
├── build_rollups.py        rebuild tsa_daily_by_airport, enplanements_monthly_by_airport, airport_pax_daily
└── cache/
    ├── tsa-foia/           weekly PDFs (~2 GB)
    └── bts-t100/           annual zips (~80 MB)
```

## Refresh

```bash
# TSA public (national totals)
node scripts/refresh.mjs

# TSA FOIA per-airport (~ weekly PDFs)
uv run --with pdfplumber python3 db/ingest_tsa_foia.py

# BTS T-100 (annual zips)
node db/download_bts_t100.mjs --from 2019 --to "$(date +%Y)"
python3 db/ingest_bts_t100.py

# Rebuild rollups after any of the above
python3 db/build_rollups.py
```

The TSA FOIA ingest is **idempotent** — it skips weeks whose `covers_from`
date already has rows in `tsa_hourly`. Re-running picks up new weeklies and
any previously failed parses (the parser was upgraded to pdfplumber to handle
the 2019–2021 "PMIS - Total Customer Throughput" layout in addition to the
2022+ "Total Pax + KCM PAX" layout).

## Key tables

See `schema.sql` for the full DDL — and `../src/lib/schema.ts` for the
matching TypeScript types.

- `airport` — IATA-keyed dimension. `dot_airport_id` populated from T-100.
- `checkpoint` — `(airport_iata, name)` unique.
- `carrier` — keyed by BTS `UNIQUE_CARRIER` (disambiguates code reuse).
- `tsa_hourly` — `(date, hour, checkpoint_id) → pax_incl_kcm`. The native TSA
  FOIA grain. **KCM (Known Crewmember) pass-throughs are included**, per the
  source. Total is ~10–12% lower than the TSA public counter at the national
  level — the FOIA report's scope is narrower (excludes some non-checkpoint
  screenings the public counter rolls in).
- `tsa_daily_national` — daily totals from the public TSA page. Includes
  pre-FOIA history that the per-checkpoint data doesn't cover.
- `t100_segment` — BTS T-100 raw segment rows. **Domestic Segment (U.S.
  Carriers)** only — international flights are out of scope for this project.
- `enplanements_monthly_by_airport` — rollup: passengers by origin airport
  and month, filtered to passenger-class service (`F,L,A,C,E,P`) and
  passenger aircraft configuration (`aircraft_config=1`).
- `airport_pax_daily` — unified daily fact across all metrics. T-100 monthly
  totals are _apportioned uniformly_ to days (`granularity='month_apportioned',
is_estimated=1`) for queryability; do not trust per-day values from this
  source. TSA values are `granularity='day', is_estimated=0`.
- `ingest_run` — provenance: every load creates a row with source URL,
  filename, fetched timestamp, row count, and the date range it covers.

## Known gaps / caveats

- International flights are deliberately out of scope. `t100_segment` covers
  only the BTS T-100 Domestic Segment dataset (U.S. carriers, both endpoints
  in the U.S./territories). Inbound/outbound international segments and
  foreign carriers are not loaded.
- The "TSA daily national" total is **~10–15% higher** than the sum of
  `tsa_hourly` across all checkpoints. The two are distinct reports.
