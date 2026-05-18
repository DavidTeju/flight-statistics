<script lang="ts">
	import { resolve } from '$app/paths';
	import '../app.css';
	let { children } = $props();
</script>

<div class="shell">
	<header class="topbar">
		<a class="brand" href={resolve('/')} aria-label="Flight Statistics — home">
			<svg class="mark" viewBox="0 0 32 32" aria-hidden="true">
				<rect width="32" height="32" rx="6" fill="#F4F1E8" />
				<rect x="4" y="4" width="4" height="4" rx="0.8" fill="#EDEBD8" />
				<rect x="9" y="4" width="4" height="4" rx="0.8" fill="#D6DDB6" />
				<rect x="14" y="4" width="4" height="4" rx="0.8" fill="#B9C98F" />
				<rect x="19" y="4" width="4" height="4" rx="0.8" fill="#97B468" />
				<rect x="24" y="4" width="4" height="4" rx="0.8" fill="#739A4B" />
				<rect x="4" y="9" width="4" height="4" rx="0.8" fill="#D6DDB6" />
				<rect x="9" y="9" width="4" height="4" rx="0.8" fill="#B9C98F" />
				<rect x="14" y="9" width="4" height="4" rx="0.8" fill="#97B468" />
				<rect x="19" y="9" width="4" height="4" rx="0.8" fill="#739A4B" />
				<rect x="24" y="9" width="4" height="4" rx="0.8" fill="#4F7A35" />
				<rect x="4" y="14" width="4" height="4" rx="0.8" fill="#B9C98F" />
				<rect x="9" y="14" width="4" height="4" rx="0.8" fill="#97B468" />
				<rect x="14" y="14" width="4" height="4" rx="0.8" fill="#E8553A" />
				<rect x="19" y="14" width="4" height="4" rx="0.8" fill="#4F7A35" />
				<rect x="24" y="14" width="4" height="4" rx="0.8" fill="#2E5023" />
				<rect x="4" y="19" width="4" height="4" rx="0.8" fill="#97B468" />
				<rect x="9" y="19" width="4" height="4" rx="0.8" fill="#739A4B" />
				<rect x="14" y="19" width="4" height="4" rx="0.8" fill="#4F7A35" />
				<rect x="19" y="19" width="4" height="4" rx="0.8" fill="#2E5023" />
				<rect x="24" y="19" width="4" height="4" rx="0.8" fill="#739A4B" />
				<rect x="4" y="24" width="4" height="4" rx="0.8" fill="#739A4B" />
				<rect x="9" y="24" width="4" height="4" rx="0.8" fill="#4F7A35" />
				<rect x="14" y="24" width="4" height="4" rx="0.8" fill="#2E5023" />
				<rect x="19" y="24" width="4" height="4" rx="0.8" fill="#4F7A35" />
				<rect x="24" y="24" width="4" height="4" rx="0.8" fill="#739A4B" />
			</svg>
			<span class="title display">Flight Statistics</span>
		</a>
		<div class="meta mono">
			<span class="meta-pill">DAILY · US PASSENGERS</span>
			<span class="meta-pill">TSA CHECKPOINTS</span>
		</div>
	</header>

	<main>{@render children()}</main>

	<footer class="footnote">
		<span class="mono">data · TSA.gov · passenger volumes · refreshed manually</span>
	</footer>
</div>

<style>
	.shell {
		min-height: 100vh;
		display: grid;
		grid-template-rows: auto 1fr auto;
	}

	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 11px 32px;
		border-bottom: 1px solid var(--rule);
		background: var(--bg-2);
		position: sticky;
		top: 0;
		z-index: 10;
		backdrop-filter: blur(8px);
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 10px;
		color: var(--ink);
	}

	.mark {
		width: 28px;
		height: 28px;
		display: block;
		border: 1px solid var(--rule);
		border-radius: 6px;
	}

	.title {
		font-size: 20px;
		font-weight: 400;
		letter-spacing: 0;
		color: var(--ink);
	}

	.meta {
		display: flex;
		gap: 8px;
	}

	.meta-pill {
		font-size: 10px;
		letter-spacing: 0.2em;
		color: var(--ink-dim);
		padding: 5px 9px;
		border: 1px solid var(--rule);
		border-radius: 999px;
		background: var(--bg-2);
	}

	main {
		padding: 0;
		min-height: 0;
	}

	.footnote {
		padding: 8px 32px;
		border-top: 1px solid var(--rule);
		color: var(--ink-faint);
		font-size: 11px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	@media (max-width: 720px) {
		.topbar {
			padding: 9px 18px;
		}
		.title {
			font-size: 17px;
		}
		.mark {
			width: 24px;
			height: 24px;
		}
		.meta-pill {
			font-size: 9px;
		}
	}
</style>
