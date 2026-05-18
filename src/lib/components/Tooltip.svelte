<script lang="ts">
	import { fmtFull } from '$lib/format';

	type Props = {
		visible: boolean;
		x: number;
		y: number;
		title: string;
		subtitle: string;
		value: number;
	};

	let { visible, x, y, title, subtitle, value }: Props = $props();
</script>

{#if visible}
	<div class="tip" style="left:{x}px; top:{y}px" role="tooltip">
		<div class="card">
			<div class="title">{title}</div>
			<div class="value mono">{fmtFull(value)}</div>
			<div class="label mono">PASSENGERS</div>
			{#if subtitle}
				<div class="iso mono">{subtitle}</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.tip {
		position: fixed;
		pointer-events: none;
		transform: translate(14px, 14px);
		z-index: 100;
	}

	.card {
		background: var(--bg-2);
		color: var(--ink);
		border: 1px solid var(--rule-strong);
		border-radius: 12px;
		padding: 12px 16px 14px;
		min-width: 200px;
		box-shadow: 0 12px 32px -16px rgba(46, 64, 43, 0.28);
	}

	.title {
		font-family: var(--serif);
		font-size: 14px;
		color: var(--ink-dim);
		letter-spacing: 0;
	}

	.value {
		font-family: var(--display);
		font-size: 32px;
		font-weight: 400;
		color: var(--vermilion);
		line-height: 1.05;
		margin-top: 6px;
		letter-spacing: -0.01em;
	}

	.label {
		font-size: 9px;
		letter-spacing: 0.22em;
		color: var(--ink-faint);
		margin-top: 4px;
		text-transform: uppercase;
	}

	.iso {
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px solid var(--rule);
		font-size: 10px;
		letter-spacing: 0.08em;
		color: var(--ink-faint);
	}
</style>
