<script lang="ts">
	import { RAMP } from '$lib/colorScale';
	import { fmtCompact } from '$lib/format';

	type Props = {
		min: number;
		max: number;
		quantiles: number[];
	};

	let { min, max, quantiles }: Props = $props();
</script>

<aside class="legend" aria-label="Color legend">
	<div class="head">
		<span class="eyebrow">LEGEND</span>
		<span class="hint mono">PASSENGERS / DAY</span>
	</div>
	<div class="ramp">
		{#each RAMP as color (color)}
			<span class="swatch" style="background:{color}"></span>
		{/each}
	</div>
	<div class="ticks mono">
		<span>{fmtCompact(min)}</span>
		<span>{fmtCompact(quantiles[2])}</span>
		<span>{fmtCompact(max)}</span>
	</div>
</aside>

<style>
	.legend {
		position: fixed;
		right: 22px;
		bottom: 22px;
		z-index: 5;
		padding: 12px 14px 11px;
		border: 1px solid var(--rule-strong);
		border-radius: 12px;
		background: var(--bg-2);
		min-width: 210px;
		box-shadow: var(--shadow-lg);
	}

	.head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		margin-bottom: 8px;
	}

	.hint {
		color: var(--ink-faint);
		font-size: 9px;
		letter-spacing: 0.18em;
		text-transform: uppercase;
	}

	.ramp {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 1px;
		border-radius: 2px;
		overflow: hidden;
	}

	.swatch {
		height: 12px;
		display: block;
	}

	.ticks {
		display: flex;
		justify-content: space-between;
		margin-top: 6px;
		font-size: 10px;
		color: var(--ink-dim);
		letter-spacing: 0.04em;
	}

	@media (max-width: 720px) {
		.legend {
			right: 12px;
			bottom: 12px;
			min-width: 170px;
			padding: 10px 12px 9px;
		}
	}
</style>
