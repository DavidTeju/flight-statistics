// "Meadow Tarmac" 7-step sequential green ramp.
// Step 0 reads as drained paper (COVID floor); step 6 reads as ripe forest
// (peak summer 2024). Single hue family → colorblind-safe + one story.
export const RAMP = [
	'#EDEBD8', // 0 — pale lichen (COVID floor)
	'#D6DDB6', // 1 — sun-bleached sage
	'#B9C98F', // 2 — young leaf
	'#97B468', // 3 — meadow
	'#739A4B', // 4 — moss
	'#4F7A35', // 5 — deep moss
	'#2E5023' //  6 — forest floor (2024 peaks)
] as const;

export type Quantiles = number[]; // length 6, ascending

export function bucketIndex(value: number, breaks: Quantiles): number {
	for (let i = 0; i < breaks.length; i++) {
		if (value < breaks[i]) return i;
	}
	return breaks.length; // top bucket
}

export function colorFor(value: number, breaks: Quantiles): string {
	return RAMP[bucketIndex(value, breaks)];
}
