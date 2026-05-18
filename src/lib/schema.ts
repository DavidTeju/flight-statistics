// Canonical types for TSA checkpoint throughput + BTS T-100 enplanements.
// Mirrors db/schema.sql 1:1.

// ─── Dimensions ───────────────────────────────────────────────────────────

export type Airport = {
	iata: string; // 'ATL'. Primary key for airports we know by IATA.
	dotAirportId: number | null; // BTS OriginAirportID. Stable across IATA reuse.
	icao: string | null; // 'KATL' when known (not in either source — backfill).
	name: string; // 'Hartsfield - Jackson Atlanta International'
	city: string; // 'Atlanta'
	state: string; // 'GA' (2-letter; includes US territories like 'PR','GU','MP','VI')
	stateFips: string | null; // T-100 OriginStateFips, e.g. '13'
	cityMarketId: number | null; // T-100 OriginCityMarketID, groups DTW+YIP etc.
	wac: number | null; // T-100 OriginWac (World Area Code, country/region)
};

export type Checkpoint = {
	id: number; // surrogate
	airportIata: string; // FK → Airport.iata
	name: string; // 'Terminal 4 Main', 'CKPT-B3' — free-text from TSA
};

export type Carrier = {
	uniqueCarrier: string; // 'AA', 'PA(1)' — disambiguated; primary key
	airlineId: number; // DOT AirlineID — stable across rebrands
	iataCarrier: string | null; // raw IATA 'AA' (may be reused historically)
	name: string; // 'American Airlines Inc.'
};

// ─── TSA checkpoint throughput ────────────────────────────────────────────

// Native grain of the weekly TSA FOIA PDFs.
export type TsaHourly = {
	date: string; // 'YYYY-MM-DD' (local airport date as published)
	hour: number; // 0..23
	checkpointId: number; // FK → Checkpoint.id
	paxIncludingKcm: number; // 'Total Pax + KCM PAX' — TSA bundles KCM in
};

// Convenience rollup: airport × day, summed across checkpoints/hours.
export type TsaDailyByAirport = {
	date: string; // 'YYYY-MM-DD'
	airportIata: string;
	paxIncludingKcm: number;
};

// National rollup — replaces existing tsa_passenger_volumes.csv.
// Pre-FOIA data (2019-01-01 → first weekly PDF) lives here only; per-airport
// hourly data starts whenever TSA began publishing weeklies (~2020).
export type TsaDailyNational = {
	date: string; // 'YYYY-MM-DD'
	paxIncludingKcm: number;
	source: 'tsa_public' | 'tsa_foia_rollup';
};

// ─── BTS T-100 enplanements ───────────────────────────────────────────────

// Native grain: carrier × origin × dest × aircraft × class × month.
// Only the Domestic Segment (28DS) is loaded.
export type T100Segment = {
	year: number; // 2019..present
	month: number; // 1..12

	uniqueCarrier: string; // FK → Carrier.uniqueCarrier
	carrierRegion: string; // 'D' domestic / 'A' atlantic etc.

	originIata: string; // FK → Airport.iata (use dotAirportId for ranges)
	originAirportId: number;
	originAirportSeqId: number;
	destIata: string;
	destAirportId: number;
	destAirportSeqId: number;

	aircraftGroup: number; // BTS code
	aircraftType: number; // BTS code
	aircraftConfig: number; // 1=passenger, 2=cargo, 3=combi, 4=seaplane …
	serviceClass: string; // 'F'=scheduled passenger, 'G'=scheduled all-cargo, 'L'=non-scheduled passenger, etc.

	passengers: number; // ⭐ enplanement count, this segment, this month
	seats: number;
	depScheduled: number;
	depPerformed: number;
	freightPounds: number;
	mailPounds: number;
	distanceMiles: number;
	airTimeMinutes: number;
	rampTimeMinutes: number;
};

// Convenience rollup: airport × month enplanements (sum of passengers across
// all carriers, segments, aircraft where origin = airport AND service class
// is passenger-carrying). The thing most consumers actually want.
export type EnplanementsMonthlyByAirport = {
	year: number;
	month: number;
	airportIata: string;
	passengers: number; // sum where Origin = airport, Class ∈ passenger classes
};

// ─── Unified fact (airport × day, metric-tagged) ──────────────────────────

// Single queryable table over both sources at common grain. T-100 monthly
// totals are apportioned to days for visualization only (is_estimated=true).
export type AirportPaxDaily = {
	date: string; // 'YYYY-MM-DD'
	airportIata: string; // FK → Airport.iata. Use '__US__' for national.
	metric: 'tsa_throughput' | 'enplanements_domestic';
	passengers: number;
	source: 'tsa_foia' | 'tsa_public' | 'bts_t100';
	granularity: 'day' | 'month_apportioned';
	isEstimated: boolean;
};

// ─── Ingest provenance ────────────────────────────────────────────────────

export type IngestRun = {
	id: number;
	source: 'tsa_public' | 'tsa_foia' | 'bts_t100_domestic';
	fetchedAt: string; // ISO timestamp
	sourceUrl: string;
	sourceFilename: string | null;
	rowCount: number;
	coversFrom: string; // 'YYYY-MM-DD'
	coversTo: string;
	notes: string | null;
};
