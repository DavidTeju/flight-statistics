export type Day = {
	iso: string; // YYYY-MM-DD
	date: Date; // UTC midnight
	value: number;
	dow: number; // 0=Sun … 6=Sat
	year: number;
	month: number; // 0..11
	day: number; // 1..31
	index: number; // position in Dataset.days
};

export type Dataset = {
	days: Day[]; // sorted ascending
	byIso: Map<string, Day>;
	years: number[];
	min: number;
	max: number;
	total: number;
	minDay: Day;
	maxDay: Day;
	quantiles: number[]; // 6 breakpoints producing 7 bins
	latest: Day;
};

// 7 color buckets ↔ 6 break points at i/7 for i ∈ [1..6].
const BUCKETS = 7;
const QUANTILE_BREAKS = Array.from({ length: BUCKETS - 1 }, (_, i) => (i + 1) / BUCKETS);

function quantile(sorted: number[], q: number): number {
	const pos = (sorted.length - 1) * q;
	const lo = Math.floor(pos);
	const hi = Math.ceil(pos);
	if (lo === hi) return sorted[lo];
	return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

export function parseCsv(text: string): Dataset {
	const lines = text.split(/\r?\n/).filter((l) => l.trim().length);
	// header row is "date,passenger_volume"
	const days: Day[] = [];
	for (let i = 1; i < lines.length; i++) {
		const [iso, raw] = lines[i].split(',');
		if (!iso || !raw) continue;
		const value = Number(raw);
		if (!Number.isFinite(value)) continue;
		// Parse as UTC to avoid TZ-shift bugs in the calendar grid.
		const [y, m, d] = iso.split('-').map(Number);
		const date = new Date(Date.UTC(y, m - 1, d));
		days.push({
			iso,
			date,
			value,
			dow: date.getUTCDay(),
			year: y,
			month: m - 1,
			day: d,
			index: 0
		});
	}
	days.sort((a, b) => a.date.getTime() - b.date.getTime());

	const byIso = new Map<string, Day>();
	let minDay = days[0];
	let maxDay = days[0];
	let total = 0;
	for (let i = 0; i < days.length; i++) {
		const day = days[i];
		day.index = i;
		byIso.set(day.iso, day);
		total += day.value;
		if (day.value < minDay.value) minDay = day;
		if (day.value > maxDay.value) maxDay = day;
	}

	const values = days.map((d) => d.value).sort((a, b) => a - b);
	const quantiles = QUANTILE_BREAKS.map((q) => quantile(values, q));

	const years = Array.from(new Set(days.map((d) => d.year))).sort((a, b) => a - b);

	return {
		days,
		byIso,
		years,
		min: minDay.value,
		max: maxDay.value,
		total,
		minDay,
		maxDay,
		quantiles,
		latest: days[days.length - 1]
	};
}

export async function loadDataset(fetchFn: typeof fetch = fetch): Promise<Dataset> {
	const res = await fetchFn('/tsa_passenger_volumes.csv');
	if (!res.ok) throw new Error(`Failed to load CSV: ${res.status}`);
	const text = await res.text();
	return parseCsv(text);
}
