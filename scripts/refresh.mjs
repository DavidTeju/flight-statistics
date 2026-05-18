// Re-scrape TSA passenger volumes from 2019 → current year and rewrite the CSV.
//
// Run: node scripts/refresh.mjs
//
// TSA is behind Akamai and blocks vanilla curl/node fetch. We use a real
// browser via Playwright (chromium) to fetch the pages. Playwright must be
// installed: `npm i -D playwright-chromium && npx playwright install chromium`.

import { writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
// playwright-chromium is a manual peer install per the file header — not a project dep.
// eslint-disable-next-line n/no-extraneous-import
import { chromium } from 'playwright-chromium';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, '..', 'tsa_passenger_volumes.csv');
const CURRENT_YEAR = new Date().getUTCFullYear();
const START_YEAR = 2019;

const urls = [];
for (let y = START_YEAR; y < CURRENT_YEAR; y++) {
	urls.push({ year: y, url: `https://www.tsa.gov/travel/passenger-volumes/${y}` });
}
urls.push({ year: CURRENT_YEAR, url: 'https://www.tsa.gov/travel/passenger-volumes' });

const browser = await chromium.launch();
const ctx = await browser.newContext();
const page = await ctx.newPage();

const rows = new Map(); // iso → value
for (const { year, url } of urls) {
	process.stderr.write(`fetching ${year} … `);
	await page.goto(url, { waitUntil: 'domcontentloaded' });
	const data = await page.$$eval('table tr', (trs) =>
		trs
			.map((tr) => [...tr.querySelectorAll('td,th')].map((c) => c.textContent?.trim() ?? ''))
			.filter((c) => c.length === 2 && c[0] && c[0].toLowerCase() !== 'date')
	);
	let n = 0;
	for (const [date, num] of data) {
		const m = date.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
		if (!m) continue;
		const iso = `${m[3]}-${m[1].padStart(2, '0')}-${m[2].padStart(2, '0')}`;
		const v = Number(num.replace(/,/g, ''));
		if (!Number.isFinite(v)) continue;
		rows.set(iso, v);
		n++;
	}
	process.stderr.write(`${n} rows\n`);
}

await browser.close();

const sorted = [...rows.entries()].sort(([a], [b]) => a.localeCompare(b));
const lines = ['date,passenger_volume', ...sorted.map(([iso, v]) => `${iso},${v}`)];
writeFileSync(OUT, lines.join('\n') + '\n');
process.stderr.write(`\nwrote ${sorted.length} rows → ${OUT}\n`);
