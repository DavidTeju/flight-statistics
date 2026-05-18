<script lang="ts">
	import { parseDate, type CalendarDate, type DateValue } from '@internationalized/date';
	import { DatePicker } from 'bits-ui';

	type Props = {
		value: string; // ISO YYYY-MM-DD
		min: string;
		max: string;
		onChange: (iso: string) => void;
	};

	let { value, min, max, onChange }: Props = $props();

	const YEAR_DIGITS = 4;
	const POPOVER_OFFSET = 8;

	function toCalendarDate(iso: string): CalendarDate {
		return parseDate(iso);
	}
	function fromCalendarDate(d: DateValue): string {
		const y = String(d.year).padStart(YEAR_DIGITS, '0');
		const m = String(d.month).padStart(2, '0');
		const day = String(d.day).padStart(2, '0');
		return `${y}-${m}-${day}`;
	}

	// Year list for the dropdown — derived from min/max so users can't pick a
	// year outside the dataset's range.
	const yearOptions = $derived.by(() => {
		const minY = Number(min.slice(0, YEAR_DIGITS));
		const maxY = Number(max.slice(0, YEAR_DIGITS));
		return Array.from({ length: maxY - minY + 1 }, (_, i) => minY + i);
	});
</script>

<DatePicker.Root
	value={toCalendarDate(value)}
	minValue={toCalendarDate(min)}
	maxValue={toCalendarDate(max)}
	onValueChange={(v) => v && onChange(fromCalendarDate(v))}
>
	<DatePicker.Trigger class="bits-trigger">
		<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
			<rect
				x="1.5"
				y="3"
				width="13"
				height="11"
				rx="1.5"
				fill="none"
				stroke="currentColor"
				stroke-width="1.2"
			/>
			<line x1="1.5" x2="14.5" y1="6.5" y2="6.5" stroke="currentColor" stroke-width="1.2" />
			<line x1="5" x2="5" y1="1.5" y2="4" stroke="currentColor" stroke-width="1.2" />
			<line x1="11" x2="11" y1="1.5" y2="4" stroke="currentColor" stroke-width="1.2" />
		</svg>
		<DatePicker.Input class="bits-input">
			{#snippet children({ segments })}
				{#each segments as { part, value: segVal }, i (i)}
					<DatePicker.Segment {part} class="bits-segment">{segVal}</DatePicker.Segment>
				{/each}
			{/snippet}
		</DatePicker.Input>
	</DatePicker.Trigger>

	<DatePicker.Content sideOffset={POPOVER_OFFSET} align="end" class="bits-pop-wrap">
		<DatePicker.Calendar class="bits-calendar">
			{#snippet children({ months, weekdays })}
				<DatePicker.Header class="bits-phead">
					<DatePicker.PrevButton class="bits-nav">‹</DatePicker.PrevButton>
					<div class="bits-selects">
						<DatePicker.MonthSelect class="bits-select" monthFormat="short" />
						<DatePicker.YearSelect class="bits-select" years={yearOptions} />
					</div>
					<DatePicker.NextButton class="bits-nav">›</DatePicker.NextButton>
				</DatePicker.Header>
				{#each months as month (month.value)}
					<DatePicker.Grid class="bits-grid">
						<DatePicker.GridHead>
							<DatePicker.GridRow class="bits-dow">
								{#each weekdays as day, i (i)}
									<DatePicker.HeadCell class="bits-headcell">{day.slice(0, 1)}</DatePicker.HeadCell>
								{/each}
							</DatePicker.GridRow>
						</DatePicker.GridHead>
						<DatePicker.GridBody>
							{#each month.weeks as weekDates (weekDates[0].toString())}
								<DatePicker.GridRow class="bits-weekrow">
									{#each weekDates as date (date.toString())}
										<DatePicker.Cell {date} month={month.value} class="bits-cell">
											<DatePicker.Day class="bits-day">{date.day}</DatePicker.Day>
										</DatePicker.Cell>
									{/each}
								</DatePicker.GridRow>
							{/each}
						</DatePicker.GridBody>
					</DatePicker.Grid>
				{/each}
			{/snippet}
		</DatePicker.Calendar>
	</DatePicker.Content>
</DatePicker.Root>

<style>
	/* The bits-ui parts are unstyled, so we style every part to match Meadow Tarmac. */
	:global(.bits-trigger) {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		background: var(--bg-2);
		border: 1px solid var(--rule);
		color: var(--ink);
		padding: 6px 12px 6px 10px;
		border-radius: 999px;
		font-size: 12px;
		letter-spacing: 0.04em;
		cursor: pointer;
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
		color: var(--green-deep);
	}
	:global(.bits-trigger:hover) {
		border-color: var(--rule-strong);
		background: var(--bg-3);
	}
	:global(.bits-trigger[data-state='open']) {
		border-color: var(--green);
		background: var(--bg-3);
	}

	:global(.bits-input) {
		display: inline-flex;
		gap: 1px;
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	:global(.bits-segment) {
		padding: 0 1px;
	}
	:global(.bits-segment[data-focused]) {
		background: var(--green-bright);
		color: var(--bg-2);
		border-radius: 3px;
	}

	:global(.bits-pop-wrap) {
		z-index: 30;
	}

	:global(.bits-calendar) {
		background: var(--bg-2);
		border: 1px solid var(--rule-strong);
		border-radius: 14px;
		padding: 12px;
		min-width: 280px;
		box-shadow: var(--shadow-lg);
	}

	:global(.bits-phead) {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 8px;
		gap: 4px;
	}
	:global(.bits-selects) {
		flex: 1;
		display: flex;
		gap: 6px;
		justify-content: center;
	}
	:global(.bits-select) {
		appearance: none;
		-webkit-appearance: none;
		background: var(--bg-3);
		color: var(--ink);
		border: 1px solid var(--rule);
		border-radius: 999px;
		font-family: var(--mono);
		font-size: 11px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		padding: 4px 22px 4px 10px;
		cursor: pointer;
		background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'><path d='M3 5l3 3 3-3' fill='none' stroke='%233f5a36' stroke-width='1.4' stroke-linecap='round'/></svg>");
		background-repeat: no-repeat;
		background-position: right 6px center;
		background-size: 10px;
	}
	:global(.bits-select:hover) {
		border-color: var(--rule-strong);
		background-color: var(--bg-2);
	}
	:global(.bits-select:focus-visible) {
		outline: 2px solid var(--green);
		outline-offset: 1px;
	}
	:global(.bits-nav) {
		width: 28px;
		height: 28px;
		border-radius: 999px;
		border: 1px solid var(--rule);
		background: transparent;
		color: var(--ink);
		font-size: 14px;
		cursor: pointer;
	}
	:global(.bits-nav:hover) {
		background: var(--bg-3);
		border-color: var(--rule-strong);
	}

	:global(.bits-grid) {
		width: 100%;
		border-collapse: separate;
		border-spacing: 2px;
	}
	:global(.bits-dow) {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
	}
	:global(.bits-weekrow) {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
	}
	:global(.bits-headcell) {
		text-align: center;
		font-family: var(--mono);
		font-size: 9px;
		letter-spacing: 0.18em;
		color: var(--ink-faint);
		padding: 4px 0;
	}
	:global(.bits-cell) {
		padding: 0;
	}
	:global(.bits-day) {
		display: block;
		width: 100%;
		appearance: none;
		background: transparent;
		border: 1px solid transparent;
		color: var(--ink);
		font-family: var(--mono);
		font-size: 12px;
		font-variant-numeric: tabular-nums;
		padding: 7px 0;
		border-radius: 8px;
		cursor: pointer;
		text-align: center;
	}
	:global(.bits-day:hover:not([data-disabled])) {
		background: var(--bg-3);
	}
	:global(.bits-day[data-outside-month]) {
		color: var(--ink-faint);
	}
	:global(.bits-day[data-disabled]) {
		color: var(--ink-faint);
		opacity: 0.35;
		cursor: default;
	}
	:global(.bits-day[data-selected]) {
		background: var(--green);
		color: var(--bg-2);
		border-color: var(--green-deep);
	}
	:global(.bits-day[data-today]) {
		font-weight: 600;
	}
</style>
