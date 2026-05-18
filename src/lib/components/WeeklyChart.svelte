<script lang="ts">
	/* eslint-disable import-x/no-duplicates -- svelte/animate, /easing, /motion, /transition
	   are legitimately distinct subpath imports; they only share a .d.ts internally. */
	import { flip } from 'svelte/animate';
	import { cubicOut } from 'svelte/easing';
	import { Tween } from 'svelte/motion';
	import { fade } from 'svelte/transition';
	/* eslint-enable import-x/no-duplicates */
	import { colorFor } from '$lib/colorScale';
	import type { Day } from '$lib/data';
	import { fmtCompact, fmtDateShort, fmtDateLong, dowShort } from '$lib/format';
	import Tooltip from './Tooltip.svelte';

	type Props = {
		days: Day[]; // visible window
		quantiles: number[];
	};

	let { days, quantiles }: Props = $props();

	// Bind both container dims so the viewBox matches CSS pixels exactly — that
	// way preserveAspectRatio="none" produces a 1:1 mapping with no text distortion.
	const DEFAULT_CHART_W = 800;
	const DEFAULT_CHART_H = 360;
	let wrapW = $state(DEFAULT_CHART_W);
	let wrapH = $state(DEFAULT_CHART_H);
	const CHART_W = $derived(wrapW);
	const CHART_H = $derived(wrapH);
	const PAD_LEFT = 56;
	const PAD_RIGHT = 16;
	const PAD_TOP = 24;
	const PAD_BOTTOM = 56;
	// eslint-disable-next-line no-magic-numbers
	const BAR_STRIDE_RATIO = 60 / 78;

	// "Nice number" ladder for axis ticks — d3.scaleLinear().nice() uses the same family.
	// Half steps (1.5, 2.5, 3.5, 7.5) let the axis fit closer to data than integer-only.
	// eslint-disable-next-line no-magic-numbers
	const NICE_STEPS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7.5, 8, 10];
	const DECADE_BASE = 10;
	const HEADROOM = 1.05;
	const TARGET_TICK_INTERVALS = 6;
	const FLOOR_HEADROOM_FRACTION = 0.1;

	const STRIDE = $derived((CHART_W - PAD_LEFT - PAD_RIGHT) / Math.max(days.length, 1));
	const BAR_W = $derived(STRIDE * BAR_STRIDE_RATIO);
	const plotH = $derived(CHART_H - PAD_TOP - PAD_BOTTOM);

	const MIN_LABEL_PX = 50;
	const labelEvery = $derived(Math.max(1, Math.ceil(MIN_LABEL_PX / STRIDE)));

	const windowMax = $derived(days.length ? Math.max(...days.map((d) => d.value)) : 1);
	const windowMin = $derived(days.length ? Math.min(...days.map((d) => d.value)) : 0);
	const windowRange = $derived(Math.max(windowMax - windowMin, 1));

	// Pick a "nice" tick step from a target step. Snaps to the NICE_STEPS ladder
	// scaled by the appropriate decade.
	function niceStep(target: number): number {
		if (target <= 0) return 1;
		const exp = Math.floor(Math.log10(target));
		const base = Math.pow(DECADE_BASE, exp);
		const norm = target / base;
		const nice = NICE_STEPS.find((s) => s >= norm) ?? DECADE_BASE;
		return nice * base;
	}

	// d3-style nice range: pick step, then floor min / ceil max to step boundaries.
	// Guarantees yBase and yTop both land on the same tick ladder so labels are clean.
	function niceRange(min: number, max: number): { base: number; top: number; step: number } {
		const step = niceStep((max - min) / TARGET_TICK_INTERVALS);
		const base = Math.floor(min / step) * step;
		let top = Math.ceil(max / step) * step;
		if (top <= base) top = base + step;
		return { base, top, step };
	}

	// Window-local floor with 10% headroom below windowMin, nice-snapped + tweened
	// so panning animates smoothly rather than jumping the y-axis.
	const axis = $derived(
		niceRange(windowMin - windowRange * FLOOR_HEADROOM_FRACTION, windowMax * HEADROOM)
	);
	const yBase = $derived(axis.base);
	const yTop = $derived(axis.top);
	const tickCount = $derived(Math.round((yTop - yBase) / axis.step) + 1);
	const ticks = $derived(Array.from({ length: tickCount }, (_, i) => yBase + axis.step * i));

	const NICE_Y_TWEEN_MS = 560;
	const TWEEN_MS = 280;
	const yTopTween = Tween.of(() => yTop, { duration: NICE_Y_TWEEN_MS, easing: cubicOut });
	const yBaseTween = Tween.of(() => yBase, { duration: NICE_Y_TWEEN_MS, easing: cubicOut });

	function yFor(value: number): number {
		const top = yTopTween.current;
		const base = yBaseTween.current;
		if (top === base) return PAD_TOP + plotH;
		return PAD_TOP + plotH * (1 - (value - base) / (top - base));
	}
	function xFor(i: number): number {
		return PAD_LEFT + i * STRIDE;
	}

	let hover = $state<{ day: Day | null; x: number; y: number }>({
		day: null,
		x: 0,
		y: 0
	});

	function onEnter(e: PointerEvent, day: Day) {
		hover = { day, x: e.clientX, y: e.clientY };
	}
	function onMove(e: PointerEvent) {
		if (!hover.day) return;
		hover = { ...hover, x: e.clientX, y: e.clientY };
	}
	function onLeave() {
		hover = { day: null, x: 0, y: 0 };
	}

	const TICK_LABEL_OFFSET_X = 10;
	const TICK_LABEL_OFFSET_Y = 4;
	const BAR_HALF = $derived(BAR_W / 2);
	const VALUE_LABEL_OFFSET = 8;
	const DOW_LABEL_OFFSET = 30;
	const DATE_LABEL_OFFSET = 14;
	const FADE_IN_MS = 440;
	const FADE_OUT_MS = 320;
	const BAR_FADE_IN_MS = 200;
	const BAR_FADE_OUT_MS = 140;
	const DOW_SAT = 0;
	const DOW_SUN = 6;

	// Stable key for the axis crossfade — fires when either bound changes.
	const axisKey = $derived(`${yBase}-${yTop}`);
</script>

<div class="chart-wrap">
	<svg
		class="chart"
		bind:clientWidth={wrapW}
		bind:clientHeight={wrapH}
		viewBox="0 0 {CHART_W} {CHART_H}"
		preserveAspectRatio="none"
		role="img"
		aria-label="Bar chart of daily passenger volumes"
	>
		{#key axisKey}
			<g in:fade={{ duration: FADE_IN_MS }} out:fade={{ duration: FADE_OUT_MS }}>
				{#each ticks as t (t)}
					<line
						x1={PAD_LEFT}
						x2={CHART_W - PAD_RIGHT}
						y1={yFor(t)}
						y2={yFor(t)}
						stroke="var(--rule)"
						stroke-dasharray="2 4"
					/>
					<text
						x={PAD_LEFT - TICK_LABEL_OFFSET_X}
						y={yFor(t) + TICK_LABEL_OFFSET_Y}
						text-anchor="end"
						class="axis">{fmtCompact(t)}</text
					>
				{/each}
			</g>
		{/key}

		<!-- baseline -->
		<line
			x1={PAD_LEFT}
			x2={CHART_W - PAD_RIGHT}
			y1={yFor(yBaseTween.current)}
			y2={yFor(yBaseTween.current)}
			stroke="var(--rule-strong)"
		/>

		{#each days as day, i (day.iso)}
			{@const yBot = yFor(yBaseTween.current)}
			{@const yTopPx = yFor(day.value)}
			{@const yClamped = Math.max(PAD_TOP, Math.min(yTopPx, yBot))}
			{@const y = yClamped}
			{@const h = Math.max(0, yBot - y)}
			{@const showLabel = day.index % labelEvery === 0}
			<g
				class="bar-group"
				transform="translate({xFor(i)}, 0)"
				animate:flip={{ duration: TWEEN_MS, easing: cubicOut }}
				in:fade={{ duration: BAR_FADE_IN_MS }}
				out:fade={{ duration: BAR_FADE_OUT_MS }}
			>
				<rect
					x={0}
					y={PAD_TOP}
					width={BAR_W}
					height={plotH}
					fill="transparent"
					role="presentation"
					aria-hidden="true"
					onpointerenter={(e) => onEnter(e, day)}
					onpointermove={onMove}
					onpointerleave={onLeave}
				/>
				<rect
					x={0}
					{y}
					width={BAR_W}
					height={h}
					fill={colorFor(day.value, quantiles)}
					class="bar"
					class:weekend={day.dow === DOW_SAT || day.dow === DOW_SUN}
					rx="2"
					ry="2"
				/>
				{#if showLabel}
					<text x={BAR_HALF} y={y - VALUE_LABEL_OFFSET} text-anchor="middle" class="bar-value"
						>{fmtCompact(day.value)}</text
					>
					<text x={BAR_HALF} y={CHART_H - DOW_LABEL_OFFSET} text-anchor="middle" class="x-dow"
						>{dowShort(day.dow).toUpperCase()}</text
					>
					<text x={BAR_HALF} y={CHART_H - DATE_LABEL_OFFSET} text-anchor="middle" class="x-date"
						>{fmtDateShort(day.date).replace(/^[A-Z]+\s/i, '')}</text
					>
				{/if}
			</g>
		{/each}
	</svg>
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
	.chart-wrap {
		padding: 4px 24px 8px;
		width: 100%;
		height: 100%;
		min-height: 180px;
		display: flex;
	}

	.chart {
		display: block;
		width: 100%;
		height: 100%;
		min-height: 0;
		max-height: 100%;
	}

	.bar {
		transition: filter 0.18s ease;
	}
	.bar.weekend {
		opacity: 0.92;
	}
	.bar-group:hover .bar {
		filter: brightness(1.06);
	}

	.axis {
		font-family: var(--mono);
		font-size: 10px;
		fill: var(--ink-faint);
		letter-spacing: 0.04em;
	}
	.bar-value {
		font-family: var(--mono);
		font-size: 10px;
		fill: var(--ink-dim);
		letter-spacing: 0.04em;
	}
	.x-dow {
		font-family: var(--mono);
		font-size: 9px;
		fill: var(--ink-faint);
		letter-spacing: 0.22em;
	}
	.x-date {
		font-family: var(--mono);
		font-size: 11px;
		fill: var(--ink);
		letter-spacing: 0.04em;
	}
</style>
