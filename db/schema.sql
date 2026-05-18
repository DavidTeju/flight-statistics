-- Flight Statistics — canonical schema for TSA checkpoint throughput
-- and BTS T-100 enplanements. Mirrors src/lib/schema.ts.
--
-- Target: SQLite (single-file, fits the app). Postgres-compatible aside from
-- AUTOINCREMENT and TEXT vs VARCHAR — note differences inline.

PRAGMA foreign_keys = ON;

-- ─── Dimensions ──────────────────────────────────────────────────────────

CREATE TABLE airport (
    iata             TEXT PRIMARY KEY,            -- 'ATL'
    -- BTS OriginAirportID. Not UNIQUE — BTS reuses an airport_id across
    -- different IATAs over time (e.g. when a code is decommissioned and
    -- assigned to a new airport years later).
    dot_airport_id   INTEGER,
    icao             TEXT,                        -- 'KATL' (backfilled, optional)
    name             TEXT NOT NULL,
    city             TEXT NOT NULL,
    state            TEXT NOT NULL,               -- 'GA', 'PR', 'GU', 'MP', 'VI'
    state_fips       TEXT,
    city_market_id   INTEGER,
    wac              INTEGER
);

CREATE INDEX airport_state_idx        ON airport(state);
CREATE INDEX airport_city_market_idx  ON airport(city_market_id);
CREATE INDEX airport_dot_id_idx       ON airport(dot_airport_id);

CREATE TABLE checkpoint (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_iata  TEXT NOT NULL REFERENCES airport(iata),
    name          TEXT NOT NULL,
    UNIQUE (airport_iata, name)
);

CREATE INDEX checkpoint_airport_idx ON checkpoint(airport_iata);

CREATE TABLE carrier (
    unique_carrier   TEXT PRIMARY KEY,            -- 'AA', 'PA(1)'
    airline_id       INTEGER NOT NULL,            -- stable DOT id
    iata_carrier     TEXT,                        -- raw IATA, may be reused
    name             TEXT NOT NULL
);

CREATE INDEX carrier_airline_id_idx ON carrier(airline_id);

-- ─── TSA checkpoint throughput ───────────────────────────────────────────

-- Native FOIA grain. ~ (n_checkpoints × n_days × 24) rows; ballpark a few
-- million per year. INTEGER pax handles KCM-inclusive 'Total Pax + KCM PAX'.
CREATE TABLE tsa_hourly (
    date              TEXT NOT NULL,               -- 'YYYY-MM-DD'
    hour              INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    checkpoint_id     INTEGER NOT NULL REFERENCES checkpoint(id),
    pax_incl_kcm      INTEGER NOT NULL CHECK (pax_incl_kcm >= 0),
    ingest_run_id     INTEGER REFERENCES ingest_run(id),
    PRIMARY KEY (date, hour, checkpoint_id)
);

CREATE INDEX tsa_hourly_date_idx       ON tsa_hourly(date);
CREATE INDEX tsa_hourly_checkpoint_idx ON tsa_hourly(checkpoint_id, date);

-- Materialized rollup: airport × day. Refreshed after each FOIA ingest.
CREATE TABLE tsa_daily_by_airport (
    date            TEXT NOT NULL,
    airport_iata    TEXT NOT NULL REFERENCES airport(iata),
    pax_incl_kcm    INTEGER NOT NULL,
    PRIMARY KEY (date, airport_iata)
);

CREATE INDEX tsa_daily_by_airport_iata_idx ON tsa_daily_by_airport(airport_iata, date);

-- National daily — replaces existing tsa_passenger_volumes.csv.
-- Pre-FOIA history (2019 → first weekly PDF) only exists at this level.
CREATE TABLE tsa_daily_national (
    date           TEXT PRIMARY KEY,               -- 'YYYY-MM-DD'
    pax_incl_kcm   INTEGER NOT NULL,
    source         TEXT NOT NULL CHECK (source IN ('tsa_public', 'tsa_foia_rollup'))
);

-- ─── BTS T-100 enplanements ──────────────────────────────────────────────

-- Native segment grain. Domestic Segment only. ~150k–300k rows per month.
CREATE TABLE t100_segment (
    year                  INTEGER NOT NULL,
    month                 INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),

    unique_carrier        TEXT NOT NULL REFERENCES carrier(unique_carrier),
    carrier_region        TEXT NOT NULL,

    origin_iata           TEXT NOT NULL,           -- soft FK (IATA may be reused over years)
    origin_airport_id     INTEGER NOT NULL,        -- hard FK candidate
    origin_airport_seq_id INTEGER NOT NULL,
    dest_iata             TEXT NOT NULL,
    dest_airport_id       INTEGER NOT NULL,
    dest_airport_seq_id   INTEGER NOT NULL,

    aircraft_group        INTEGER NOT NULL,
    aircraft_type         INTEGER NOT NULL,
    aircraft_config       INTEGER NOT NULL,
    service_class         TEXT NOT NULL,           -- 'F','G','L','P','Q', etc.

    passengers            INTEGER NOT NULL CHECK (passengers >= 0),
    seats                 INTEGER NOT NULL,
    dep_scheduled         INTEGER NOT NULL,
    dep_performed         INTEGER NOT NULL,
    freight_lb            INTEGER NOT NULL,
    mail_lb               INTEGER NOT NULL,
    distance_mi           INTEGER NOT NULL,
    air_time_min          INTEGER NOT NULL,
    ramp_time_min         INTEGER NOT NULL,

    ingest_run_id         INTEGER REFERENCES ingest_run(id),

    -- T-100 can have multiple rows for the same (carrier, o/d, aircraft, class, month)
    -- if reported separately, so we use a surrogate.
    id                    INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE INDEX t100_origin_idx    ON t100_segment(origin_iata, year, month);
CREATE INDEX t100_dest_idx      ON t100_segment(dest_iata,   year, month);
CREATE INDEX t100_carrier_idx   ON t100_segment(unique_carrier, year, month);
CREATE INDEX t100_year_month_idx ON t100_segment(year, month);

-- Materialized rollup: airport × month enplanements (origin side, passenger classes).
CREATE TABLE enplanements_monthly_by_airport (
    year          INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    airport_iata  TEXT NOT NULL REFERENCES airport(iata),
    passengers    INTEGER NOT NULL,
    PRIMARY KEY (year, month, airport_iata)
);

CREATE INDEX enplanements_airport_idx ON enplanements_monthly_by_airport(airport_iata, year, month);

-- ─── Unified daily fact ──────────────────────────────────────────────────

-- One table for viz/analytics over both sources at a common grain.
-- T-100 monthly figures are apportioned to days for display only.
CREATE TABLE airport_pax_daily (
    date            TEXT NOT NULL,                 -- 'YYYY-MM-DD'
    airport_iata    TEXT NOT NULL,                 -- '__US__' for national rollup
    metric          TEXT NOT NULL CHECK (metric IN (
                        'tsa_throughput',
                        'enplanements_domestic'
                    )),
    passengers      INTEGER NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('tsa_foia','tsa_public','bts_t100')),
    granularity     TEXT NOT NULL CHECK (granularity IN ('day','month_apportioned')),
    is_estimated    INTEGER NOT NULL CHECK (is_estimated IN (0,1)),
    PRIMARY KEY (date, airport_iata, metric)
);

CREATE INDEX airport_pax_daily_airport_idx ON airport_pax_daily(airport_iata, date);
CREATE INDEX airport_pax_daily_metric_idx  ON airport_pax_daily(metric, date);

-- ─── Provenance ──────────────────────────────────────────────────────────

CREATE TABLE ingest_run (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT NOT NULL CHECK (source IN (
                          'tsa_public','tsa_foia','bts_t100_domestic'
                      )),
    fetched_at        TEXT NOT NULL,               -- ISO-8601
    source_url        TEXT NOT NULL,
    source_filename   TEXT,
    row_count         INTEGER NOT NULL,
    covers_from       TEXT NOT NULL,
    covers_to         TEXT NOT NULL,
    notes             TEXT
);

CREATE INDEX ingest_run_source_idx ON ingest_run(source, fetched_at);

-- ─── Convenience views ───────────────────────────────────────────────────

-- National TSA throughput (FOIA-derived when available, falls back to public scrape).
CREATE VIEW v_tsa_daily_national AS
SELECT date, pax_incl_kcm, source FROM tsa_daily_national;

-- Airport-day TSA throughput including hourly-source dates.
CREATE VIEW v_airport_day_tsa AS
SELECT date, airport_iata, pax_incl_kcm AS passengers
FROM   tsa_daily_by_airport;

-- Airport-month enplanements (Domestic Segment).
CREATE VIEW v_airport_month_enplanements AS
SELECT year, month, airport_iata, passengers
FROM   enplanements_monthly_by_airport;
