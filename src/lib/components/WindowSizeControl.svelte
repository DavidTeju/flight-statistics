<script lang="ts">
	type Props = {
		size: number;
		onChange: (n: number) => void;
	};
	let { size, onChange }: Props = $props();
	// eslint-disable-next-line no-magic-numbers
	const OPTIONS = [7, 14, 20];
</script>

<div class="ctl" role="radiogroup" aria-label="Window size in days">
	<span class="eyebrow lbl">WINDOW</span>
	{#each OPTIONS as n (n)}
		<button
			type="button"
			role="radio"
			aria-checked={size === n}
			class="opt mono"
			class:active={size === n}
			onclick={() => onChange(n)}
		>
			{n}d
		</button>
	{/each}
</div>

<style>
	.ctl {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 5px 6px 5px 12px;
		border: 1px solid var(--rule);
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.02);
	}
	.lbl {
		color: var(--ink-faint);
		font-size: 10px;
		margin-right: 4px;
	}
	.opt {
		border: 0;
		background: transparent;
		color: var(--ink-dim);
		padding: 6px 10px;
		border-radius: 999px;
		font-size: 12px;
		letter-spacing: 0.08em;
		cursor: pointer;
		transition:
			background 0.15s ease,
			color 0.15s ease;
	}
	.opt:hover {
		color: var(--ink);
	}
	.opt.active {
		background: var(--green);
		color: var(--bg-2);
		font-weight: 500;
	}
</style>
