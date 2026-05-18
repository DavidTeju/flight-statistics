// Drive the BTS TranStats form to download T-100 Domestic Segment zips
// for each year 2019..present. Saves into db/cache/bts-t100/.
//
// Usage:  node db/download_bts_t100.mjs [--from 2019] [--to 2026]

import { mkdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-chromium';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CACHE = join(__dirname, 'cache', 'bts-t100');
mkdirSync(CACHE, { recursive: true });

const args = Object.fromEntries(
	process.argv.slice(2).reduce((acc, v, i, arr) => {
		if (v.startsWith('--')) acc.push([v.slice(2), arr[i + 1]]);
		return acc;
	}, [])
);
const FROM = Number(args.from ?? 2019);
const TO = Number(args.to ?? new Date().getUTCFullYear());

// T-100 Domestic Segment (US Carriers).
const DATASETS = [
	{
		key: 't100_domestic',
		url: 'https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FIM&QO_fu146_anzr=Nv4%20Pn44vr45'
	}
];

const UA =
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const browser = await chromium.launch();
const ctx = await browser.newContext({ userAgent: UA, acceptDownloads: true });

async function waitForFormReady(page) {
	// After each postback, wait until the canonical controls are back in the DOM.
	await page.waitForSelector('#btnDownload', { state: 'attached', timeout: 60000 });
	await page.waitForSelector('#cboYear', { state: 'attached', timeout: 60000 });
	await page.waitForSelector('#chkAllVars', { state: 'attached', timeout: 60000 });
}

async function postback(page, controlName) {
	// Some checkboxes live inside a collapsed accordion (display:none on a
	// parent SPAN), so a regular .click() fails. Set checked=true via JS and
	// fire the canonical postback the form already wires up to that control.
	const navP = page
		.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 30000 })
		.catch(() => null);
	await page.evaluate((n) => {
		const el = document.getElementById(n);
		if (el && 'checked' in el) el.checked = true;
		window.__doPostBack(n, '');
	}, controlName);
	await navP;
	await waitForFormReady(page);
}

async function downloadOne(page, year, datasetUrl, outPath) {
	if (existsSync(outPath) && statSync(outPath).size > 5000) {
		console.error(`  skip ${outPath} (already exists)`);
		return true;
	}
	await page.goto(datasetUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
	await waitForFormReady(page);

	// selectOption auto-fires onchange which posts back to the server.
	const navP1 = page
		.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 30000 })
		.catch(() => null);
	await page.selectOption('#cboYear', String(year));
	await navP1;
	await waitForFormReady(page);

	await postback(page, 'chkAllVars');
	await postback(page, 'chkDownloadZip');

	const dlPromise = page.waitForEvent('download', { timeout: 240000 });
	// btnDownload may also be inside a collapsed section, so click via JS.
	await page.evaluate(() => {
		const btn = document.getElementById('btnDownload');
		if (btn) btn.click();
	});
	const dl = await dlPromise;
	await dl.saveAs(outPath);
	const sz = statSync(outPath).size;
	console.error(`  saved ${outPath} (${sz.toLocaleString()} bytes)`);
	return sz > 5000;
}

for (const { key, url } of DATASETS) {
	console.error(`\n=== ${key} ===`);
	const page = await ctx.newPage();
	for (let y = FROM; y <= TO; y++) {
		const out = join(CACHE, `${key}_${y}.zip`);
		try {
			await downloadOne(page, y, url, out);
		} catch (e) {
			console.error(`  ${key} ${y} FAIL: ${e.message}`);
		}
	}
	await page.close();
}

await browser.close();
console.error('\ndone.');
