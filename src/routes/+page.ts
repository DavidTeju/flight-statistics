import { loadDataset } from '$lib/data';

export const prerender = true;
export const ssr = false; // CSR — we fetch the CSV in the browser

export async function load({ fetch }) {
	const dataset = await loadDataset(fetch);
	return { dataset };
}
