import { loadDataset } from '$lib/data';

export const prerender = true;
export const ssr = false;

export async function load({ fetch, url }) {
	const dataset = await loadDataset(fetch);
	const dateParam = url.searchParams.get('date');
	const sizeParam = url.searchParams.get('size');
	return {
		dataset,
		initialDate: dateParam && dataset.byIso.has(dateParam) ? dateParam : dataset.latest.iso,
		initialSize: sizeParam ? Number(sizeParam) : null
	};
}
