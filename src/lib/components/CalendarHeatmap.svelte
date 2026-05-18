<script lang="ts">
	import { SvelteMap, SvelteSet } from 'svelte/reactivity';
	import { colorFor } from '$lib/colorScale';
	import type { Dataset, Day } from '$lib/data';
	import { fmtFull, fmtMonthShort, dowLetter, fmtDateLong } from '$lib/format';
	import Tooltip from './Tooltip.svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	type Props = { dataset: Dataset };
	let { dataset }: Props = $props();

	const CELL = 13;
	const GAP = 3;
	const STRIDE = CELL + GAP;
	const ROWS = 7;
	const MAX_COLS = 53;
	const LABEL_TOP = 22;
	const LABEL_LEFT = 16;
	const GRID_W = MAX_COLS * STRIDE;
	const GRID_H = ROWS * STRIDE;
	const DOW_LABEL_X = -4;

	// Day/calendar math constants
	const MS_PER_DAY = 86_400_000;
	const DAYS_PER_WEEK = 7;
	const FIRST_WEEK_DAY_MAX = 7;
	const STAGGER_MS = 80;
	const MONTH_LABEL_Y = -7;
	const DOW_INDICES = Array.from({ length: DAYS_PER_WEEK }, (_, i) => i);

	type Cell = {
		day: Day;
		col: number;
		row: number;
		x: number;
		y: number;
	};

	type YearLayout = {
		year: number;
		cells: Cell[];
		monthLabels: { x: number; label: string }[];
		total: number;
		avg: number;
		cols: number; // number of week columns actually used
	};

	const layouts: YearLayout[] = $derived.by(() => {
		const byYear = new SvelteMap<number, Day[]>();
		for (const day of dataset.days) {
			const list = byYear.get(day.year) ?? [];
			list.push(day);
			byYear.set(day.year, list);
		}
		return dataset.years
			.slice()
			.reverse()
			.map((year) => {
				const days = byYear.get(year) ?? [];
				const jan1Dow = new Date(Date.UTC(year, 0, 1)).getUTCDay();
				const cells: Cell[] = [];
				const seenMonths = new SvelteSet<number>();
				const monthLabels: { x: number; label: string }[] = [];
				let total = 0;
				let maxCol = 0;
				for (let i = 0; i < days.length; i++) {
					const day = days[i];
					const indexInYear = (day.date.getTime() - Date.UTC(year, 0, 1)) / MS_PER_DAY;
					const col = Math.floor((indexInYear + jan1Dow) / DAYS_PER_WEEK);
					const row = day.dow;
					cells.push({
						day,
						col,
						row,
						x: col * STRIDE,
						y: row * STRIDE
					});
					total += day.value;
					if (col > maxCol) maxCol = col;
					if (day.day <= FIRST_WEEK_DAY_MAX && !seenMonths.has(day.month)) {
						seenMonths.add(day.month);
						monthLabels.push({ x: col * STRIDE, label: fmtMonthShort(day.month) });
					}
				}
				return {
					year,
					cells,
					monthLabels,
					total,
					avg: total / days.length,
					cols: maxCol + 1
				};
			});
	});

	// Tooltip state
	let hover = $state<{ day: Day | null; x: number; y: number }>({
		day: null,
		x: 0,
		y: 0
	});

	function onCellEnter(event: PointerEvent, cell: Cell) {
		hover = { day: cell.day, x: event.clientX, y: event.clientY };
	}
	function onCellMove(event: PointerEvent) {
		if (!hover.day) return;
		hover = { ...hover, x: event.clientX, y: event.clientY };
	}
	function onCellLeave() {
		hover = { day: null, x: 0, y: 0 };
	}
	function gotoDay(day: Day) {
		// SvelteKit's resolve() doesn't accept query strings; the route part IS resolved.
		// eslint-disable-next-line svelte/no-navigation-without-resolve
		void goto(`${resolve('/week')}?date=${day.iso}`);
	}
	function onCellKey(event: KeyboardEvent, day: Day) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			gotoDay(day);
		}
	}

	// Identify the latest cell for the gentle pulse
	const latestIso = $derived(dataset.latest.iso);
</script>

<div class="cal">
	{#each layouts as block, blockIdx (block.year)}
		<section class="year" style="--stagger:{blockIdx * STAGGER_MS}ms">
			<header class="year-head">
				<div class="year-label">
					<span class="display year-num">{block.year}</span>
					<span class="eyebrow year-meta">
						{fmtFull(block.total)} <span class="dim">total</span>
					</span>
				</div>
			</header>
			<div class="grid-wrap">
				<svg
					class="grid"
					viewBox="-{LABEL_LEFT} -{LABEL_TOP} {GRID_W + LABEL_LEFT} {GRID_H + LABEL_TOP}"
					preserveAspectRatio="xMinYMid meet"
					role="img"
					aria-label="Daily passenger volume for {block.year}"
				>
					<!-- month labels -->
					{#each block.monthLabels as ml (ml.label)}
						<text class="month-label" x={ml.x} y={MONTH_LABEL_Y} fill="var(--ink-faint)"
							>{ml.label}</text
						>
					{/each}
					<!-- day-of-week labels -->
					{#each DOW_INDICES as i (i)}
						<text
							class="dow-label"
							x={DOW_LABEL_X}
							y={i * STRIDE + CELL / 2}
							text-anchor="end"
							dominant-baseline="middle"
							fill="var(--ink-faint)">{dowLetter(i)}</text
						>
					{/each}
					<!-- cells -->
					{#each block.cells as cell (cell.day.iso)}
						<rect
							x={cell.x}
							y={cell.y}
							width={CELL}
							height={CELL}
							rx="2"
							ry="2"
							fill={colorFor(cell.day.value, dataset.quantiles)}
							class="cell"
							class:latest={cell.day.iso === latestIso}
							role="button"
							tabindex="0"
							aria-label="{fmtDateLong(cell.day.date)}, {fmtFull(cell.day.value)} passengers"
							onpointerenter={(e) => onCellEnter(e, cell)}
							onpointermove={onCellMove}
							onpointerleave={onCellLeave}
							onclick={() => gotoDay(cell.day)}
							onkeydown={(e) => onCellKey(e, cell.day)}
						/>
					{/each}
				</svg>
			</div>
		</section>
	{/each}
</div>

<Tooltip
	visible={!!hover.day}
	x={hover.x}
	y={hover.y}
	title={hover.day ? fmtDateLong(hover.day.date) : ''}
	subtitle={hover.day ? hover.day.iso : ''}
	value={hover.day?.value ?? 0}
/>

<style>
	.cal {
		display: flex;
		flex-direction: column;
		gap: 28px;
		padding: 24px 36px 120px 36px;
		position: relative;
	}

	.year {
		display: grid;
		grid-template-columns: 140px 1fr;
		gap: 18px;
		align-items: start;
		opacity: 0;
		transform: translateY(8px);
		animation: rise 0.7s cubic-bezier(0.2, 0.7, 0.2, 1) forwards;
		animation-delay: var(--stagger);
	}

	@keyframes rise {
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.year-head {
		padding-top: 18px;
		display: flex;
		align-items: flex-start;
	}

	.year-label {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.year-num {
		font-size: 34px;
		font-weight: 400;
		color: var(--ink);
		text-shadow: none;
		line-height: 1;
	}

	.year-meta {
		font-size: 10px;
		color: var(--ink);
		letter-spacing: 0.16em;
	}

	.year-meta .dim {
		color: var(--ink-faint);
	}

	.grid-wrap {
		/* keep the cells crisp */
		image-rendering: pixelated;
		padding-bottom: 6px;
		width: 100%;
	}

	.grid {
		width: 100%;
		height: auto;
		display: block;
	}

	/* On very tiny screens cells would become unreadably small (<5px), so allow
	   the calendar grid to scroll horizontally below the cell-readable threshold. */
	@media (max-width: 420px) {
		.grid-wrap {
			overflow-x: auto;
			overflow-y: hidden;
		}
		.grid {
			min-width: 560px;
		}
		.grid-wrap::-webkit-scrollbar {
			height: 6px;
		}
		.grid-wrap::-webkit-scrollbar-track {
			background: transparent;
		}
		.grid-wrap::-webkit-scrollbar-thumb {
			background: var(--rule);
			border-radius: 3px;
		}
	}

	.month-label {
		font-family: var(--mono);
		font-size: 10px;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		fill: var(--ink-faint);
	}

	.dow-label {
		font-family: var(--mono);
		font-size: 9px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		fill: var(--ink-faint);
	}

	.cell {
		cursor: pointer;
		transition:
			filter 0.15s ease,
			transform 0.15s ease;
		transform-origin: center;
		transform-box: fill-box;
		stroke: transparent;
		stroke-width: 1.5;
	}
	.cell:hover,
	.cell:focus-visible {
		stroke: var(--ink);
		stroke-width: 1.25;
		outline: none;
	}

	.cell.latest {
		stroke: var(--vermilion);
		stroke-width: 1.25;
	}

	@media (max-width: 720px) {
		.cal {
			padding: 16px 14px 120px;
			gap: 22px;
		}
		.year {
			grid-template-columns: 1fr;
			gap: 8px;
		}
		.year-head {
			padding-top: 0;
		}
		.year-num {
			font-size: 22px;
		}
	}
</style>
