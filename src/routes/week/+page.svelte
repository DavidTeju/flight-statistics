<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import WeeklyChart from '$lib/components/WeeklyChart.svelte';
	import WindowSizeControl from '$lib/components/WindowSizeControl.svelte';
	import { fmtFull, fmtDateLong } from '$lib/format';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	let { data } = $props();
	const dataset = $derived(data.dataset);

	// Breakpoint widths for picking a sensible default window size.
	const BP_PHONE = 768;
	const BP_LAPTOP = 1280;
	const DEFAULT_WIDTH = 1440;
	const SIZE_PHONE = 7;
	const SIZE_LAPTOP = 14;
	const SIZE_DESKTOP = 20;

	function defaultSizeForWidth(w: number): number {
		if (w < BP_PHONE) return SIZE_PHONE;
		if (w < BP_LAPTOP) return SIZE_LAPTOP;
		return SIZE_DESKTOP;
	}

	let windowSize = $state(untrack(() => data.initialSize ?? defaultSizeForWidth(DEFAULT_WIDTH)));
	let centerIso = $state(untrack(() => data.initialDate));

	let mounted = $state(false);

	// On mount, set responsive default if no URL param was given.
	onMount(() => {
		if (data.initialSize == null) {
			windowSize = defaultSizeForWidth(window.innerWidth);
		}
		mounted = true;
	});

	// Visible slice — `windowSize` bars centered on centerIso when possible.
	const visible = $derived.by(() => {
		const i = dataset.byIso.get(centerIso)?.index ?? dataset.days.length - 1;
		const half = Math.floor(windowSize / 2);
		let start = i - half;
		let end = start + windowSize;
		if (start < 0) {
			end += -start;
			start = 0;
		}
		if (end > dataset.days.length) {
			start -= end - dataset.days.length;
			end = dataset.days.length;
			if (start < 0) start = 0;
		}
		return dataset.days.slice(start, end);
	});

	const windowAvg = $derived(
		visible.reduce((s, d) => s + d.value, 0) / Math.max(visible.length, 1)
	);

	// URL sync — native replaceState so it works pre-router-init.
	$effect(() => {
		if (!mounted) return;
		const u = new URL(window.location.href);
		u.searchParams.set('date', centerIso);
		u.searchParams.set('size', String(windowSize));
		window.history.replaceState({}, '', u);
	});

	function shiftDays(n: number) {
		const cur = dataset.byIso.get(centerIso);
		if (!cur) return;
		const next = Math.max(0, Math.min(dataset.days.length - 1, cur.index + n));
		centerIso = dataset.days[next].iso;
	}

	function onPrev() {
		shiftDays(-windowSize);
	}
	function onNext() {
		shiftDays(windowSize);
	}
	function onSizeChange(n: number) {
		windowSize = n;
	}

	function onKeyDown(e: KeyboardEvent) {
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			shiftDays(e.shiftKey ? -1 : -windowSize);
		} else if (e.key === 'ArrowRight') {
			e.preventDefault();
			shiftDays(e.shiftKey ? 1 : windowSize);
		} else if (e.key === 'Escape') {
			void goto(resolve('/'));
		} else if (e.key === 'Home') {
			e.preventDefault();
			centerIso = dataset.days[0].iso;
		} else if (e.key === 'End') {
			e.preventDefault();
			centerIso = dataset.latest.iso;
		}
	}

	// Wheel + drag — only HORIZONTAL wheel/trackpad input pans the window.
	// Vertical wheel passes through so it doesn't hijack page-level scroll.
	let scrollAccum = $state(0);
	function onWheel(e: WheelEvent) {
		if (e.deltaX === 0) return;
		e.preventDefault();
		scrollAccum += e.deltaX;
		const threshold = 24;
		while (Math.abs(scrollAccum) >= threshold) {
			const dir = scrollAccum > 0 ? 1 : -1;
			shiftDays(dir);
			scrollAccum -= dir * threshold;
		}
	}

	let dragging = $state(false);
	let dragStartX = 0;
	let dragStartIso = '';
	function onPointerDown(e: PointerEvent) {
		if (e.button !== 0) return;
		dragging = true;
		dragStartX = e.clientX;
		dragStartIso = centerIso;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	}
	function onPointerMove(e: PointerEvent) {
		if (!dragging) return;
		const dx = e.clientX - dragStartX;
		const MIN_PX_PER_DAY = 40;
		const DEFAULT_PX_PER_DAY = 80;
		const pxPerDay =
			typeof window !== 'undefined'
				? Math.max(MIN_PX_PER_DAY, window.innerWidth / Math.max(windowSize, 1))
				: DEFAULT_PX_PER_DAY;
		const dayShift = -Math.round(dx / pxPerDay);
		const start = dataset.byIso.get(dragStartIso);
		if (!start) return;
		const next = Math.max(0, Math.min(dataset.days.length - 1, start.index + dayShift));
		if (dataset.days[next].iso !== centerIso) {
			centerIso = dataset.days[next].iso;
		}
	}
	function onPointerUp() {
		dragging = false;
	}

	const minIso = $derived(dataset.days[0].iso);
	const maxIso = $derived(dataset.latest.iso);
	const centerDay = $derived(dataset.byIso.get(centerIso));
</script>

<svelte:head>
	<title>{centerIso} · Flight Statistics</title>
</svelte:head>

<svelte:window onkeydown={onKeyDown} />

<div class="week-page">
	<section class="bar-strip">
		<div class="left">
			<a class="back mono" href={resolve('/')} aria-label="Back to calendar">
				<span aria-hidden="true">←</span> CALENDAR
			</a>
			<span class="divider" aria-hidden="true">·</span>
			<div class="range mono">
				{visible[0]?.iso} <span class="dim">→</span>
				{visible[visible.length - 1]?.iso}
			</div>
		</div>
		<div class="right">
			<DatePicker
				value={centerIso}
				min={minIso}
				max={maxIso}
				onChange={(iso) => (centerIso = iso)}
			/>
			<WindowSizeControl size={windowSize} onChange={onSizeChange} />
			<div class="nav">
				<button type="button" class="navbtn mono" onclick={onPrev} aria-label="Previous window"
					>‹</button
				>
				<button type="button" class="navbtn mono" onclick={onNext} aria-label="Next window"
					>›</button
				>
			</div>
		</div>
	</section>

	<section class="overview">
		<div class="centered-stat">
			<div class="centered-date mono">{centerDay ? fmtDateLong(centerDay.date) : ''}</div>
			<div class="centered-number mono">
				{centerDay ? fmtFull(centerDay.value) : '—'}
			</div>
			<div class="centered-cap mono">PASSENGERS · TSA CHECKPOINTS</div>
		</div>
		<div class="window-stats">
			<div class="stat-cell">
				<span class="eyebrow">WINDOW AVG</span>
				<span class="stat-value mono">{fmtFull(Math.round(windowAvg))}</span>
			</div>
		</div>
	</section>

	<section
		class="chart-host"
		class:dragging
		onwheel={onWheel}
		onpointerdown={onPointerDown}
		onpointermove={onPointerMove}
		onpointerup={onPointerUp}
		onpointercancel={onPointerUp}
		role="presentation"
	>
		<WeeklyChart days={visible} quantiles={dataset.quantiles} />
	</section>

	<section class="hint mono">
		<span>← →</span><span class="dim">window</span>
		<span class="sep">·</span>
		<span>shift ← →</span><span class="dim">single day</span>
		<span class="sep">·</span>
		<span>scroll / drag</span><span class="dim">pan</span>
		<span class="sep">·</span>
		<span>esc</span><span class="dim">back</span>
	</section>
</div>

<style>
	/* The week page is a vertical flex column that fills the <main> slot.
	   The chart-host flexes to fill the leftover space so the entire week
	   view fits inside the viewport without forcing a body scroll. */
	.week-page {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
	}
	/* Constrain <main> to the viewport so the week page can flex inside it
	   without overflowing. Scoped via :has() so the calendar page is unaffected. */
	:global(.shell:has(.week-page)) {
		height: 100dvh;
		min-height: 0;
	}
	:global(main:has(.week-page)) {
		height: 100%;
		min-height: 0;
		overflow: hidden;
	}

	.bar-strip {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 10px 32px;
		border-bottom: 1px solid var(--rule);
		flex-wrap: wrap;
		flex: 0 0 auto;
	}
	.left,
	.right {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.back {
		color: var(--amber);
		font-size: 11px;
		letter-spacing: 0.22em;
		text-transform: uppercase;
		transition: color 0.15s ease;
	}
	.back:hover {
		color: var(--amber-bright);
	}
	.divider {
		color: var(--ink-faint);
	}
	.range {
		color: var(--ink-dim);
		font-size: 12px;
		letter-spacing: 0.06em;
	}
	.range .dim {
		color: var(--ink-faint);
	}

	.nav {
		display: inline-flex;
		gap: 4px;
	}
	.navbtn {
		width: 30px;
		height: 30px;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: transparent;
		color: var(--ink);
		font-size: 16px;
		cursor: pointer;
		transition:
			background 0.15s ease,
			border-color 0.15s ease;
	}
	.navbtn:hover {
		background: var(--bg-3);
		border-color: var(--rule-strong);
	}

	.overview {
		display: grid;
		grid-template-columns: 1.4fr 1fr;
		gap: 24px;
		padding: 12px 40px 12px;
		align-items: end;
		border-bottom: 1px solid var(--rule);
		flex: 0 0 auto;
	}

	.centered-date {
		font-size: 12px;
		color: var(--ink-dim);
		letter-spacing: 0.16em;
		text-transform: uppercase;
		margin-top: 4px;
	}
	.centered-number {
		margin-top: 2px;
		font-size: clamp(36px, 4.5vw, 64px);
		font-family: var(--mono);
		line-height: 0.95;
		color: var(--vermilion);
		text-shadow: none;
		font-weight: 400;
		letter-spacing: -0.01em;
	}
	.centered-cap {
		margin-top: 6px;
		font-size: 10px;
		letter-spacing: 0.28em;
		color: var(--ink-faint);
	}

	.window-stats {
		display: grid;
		grid-template-columns: 1fr;
	}
	.stat-cell {
		display: flex;
		flex-direction: column;
		gap: 4px;
		padding-left: 14px;
		border-left: 1px solid var(--rule-strong);
	}
	.stat-value {
		font-size: 20px;
		color: var(--ink);
		font-weight: 500;
	}

	.chart-host {
		cursor: grab;
		touch-action: none;
		user-select: none;
		/* Generous breathing room above the chart, separating it from the
		   focused-stat header. The flex:1 below then lets the chart eat all
		   remaining vertical space. */
		padding: 36px 0 0;
		flex: 1 1 0;
		min-height: 0;
		overflow-x: auto;
		overflow-y: hidden;
		display: flex;
		align-items: stretch;
	}
	.chart-host > :global(*) {
		flex: 1 1 0;
		min-height: 0;
		min-width: 0;
		height: 100%;
	}
	.chart-host.dragging {
		cursor: grabbing;
	}

	.hint {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
		padding: 8px 32px 10px;
		font-size: 10px;
		letter-spacing: 0.18em;
		color: var(--ink);
		text-transform: uppercase;
		flex: 0 0 auto;
	}
	.hint .dim {
		color: var(--ink-faint);
	}
	.hint .sep {
		color: var(--ink-faint);
	}

	@media (max-width: 880px) {
		.overview {
			grid-template-columns: 1fr;
			gap: 16px;
			padding: 12px 22px 12px;
		}
		.bar-strip {
			padding: 10px 18px;
			gap: 10px;
		}
	}

	/* Tablet / narrow-laptop: let the header wrap onto two rows cleanly. */
	@media (max-width: 720px) {
		.bar-strip {
			padding: 10px 14px;
			gap: 8px;
		}
		.left,
		.right {
			gap: 8px;
			flex-wrap: wrap;
		}
		.range {
			font-size: 11px;
		}
	}

	/* Phone: stack the two halves so nothing gets cropped. */
	@media (max-width: 520px) {
		.bar-strip {
			flex-direction: column;
			align-items: stretch;
			padding: 10px 12px;
		}
		.left,
		.right {
			width: 100%;
			justify-content: space-between;
		}
	}
</style>
