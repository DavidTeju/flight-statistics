<script lang="ts">
	import CalendarHeatmap from '$lib/components/CalendarHeatmap.svelte';
	import Legend from '$lib/components/Legend.svelte';
	import { fmtFull, fmtDateLong } from '$lib/format';

	let { data } = $props();
	const dataset = $derived(data.dataset);

	const latest = $derived(dataset.latest);
	const max = $derived(dataset.maxDay);
	const min = $derived(dataset.minDay);
	const total = $derived(dataset.total);
</script>

<svelte:head>
	<title>Flight Statistics · TSA passenger volumes</title>
</svelte:head>

<section class="hero">
	<ul class="stats">
		<li>
			<span class="eyebrow">LATEST</span>
			<span class="stat mono">{fmtFull(latest.value)}</span>
			<span class="cap mono">{fmtDateLong(latest.date)}</span>
		</li>
		<li>
			<span class="eyebrow">ALL-TIME HIGH</span>
			<span class="stat mono">{fmtFull(max.value)}</span>
			<span class="cap mono">{fmtDateLong(max.date)}</span>
		</li>
		<li>
			<span class="eyebrow">ALL-TIME LOW</span>
			<span class="stat mono">{fmtFull(min.value)}</span>
			<span class="cap mono">{fmtDateLong(min.date)}</span>
		</li>
		<li>
			<span class="eyebrow">CUMULATIVE</span>
			<span class="stat mono">{fmtFull(total)}</span>
			<span class="cap mono">PASSENGERS SINCE 2019-01-01</span>
		</li>
	</ul>
</section>

<section class="instructions">
	<span class="eyebrow">CALENDAR · CLICK ANY DAY TO OPEN A WEEKLY VIEW</span>
</section>

<CalendarHeatmap {dataset} />

<Legend min={dataset.min} max={dataset.max} quantiles={dataset.quantiles} />

<style>
	.hero {
		padding: 22px 40px 20px;
		border-bottom: 1px solid var(--rule);
		position: relative;
	}

	.stats {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 24px;
	}

	.stats li {
		display: grid;
		grid-template-rows: auto auto auto;
		gap: 2px;
		padding-left: 16px;
		border-left: 1px solid var(--rule-strong);
	}

	.stats li:first-child {
		padding-left: 0;
		border-left: none;
	}

	.stat {
		font-size: 17px;
		color: var(--ink);
		font-weight: 500;
		margin-top: 2px;
		font-variant-numeric: tabular-nums;
	}

	.cap {
		font-size: 10px;
		color: var(--ink-faint);
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	.instructions {
		padding: 14px 40px 4px;
	}

	@media (max-width: 880px) {
		.hero {
			padding: 18px 22px 16px;
		}
		.stats {
			grid-template-columns: repeat(2, 1fr);
			gap: 14px 18px;
			row-gap: 14px;
		}
		/* When wrapped to 2 columns, each new row's first cell loses its left border. */
		.stats li:nth-child(odd) {
			padding-left: 0;
			border-left: none;
		}
		.instructions {
			padding: 12px 22px 4px;
		}
	}

	@media (max-width: 520px) {
		.stats {
			grid-template-columns: 1fr;
		}
		.stats li {
			padding-left: 0;
			border-left: none;
			padding-top: 8px;
			border-top: 1px solid var(--rule);
		}
		.stats li:first-child {
			padding-top: 0;
			border-top: none;
		}
	}
</style>
