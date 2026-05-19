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
			<a
				class="repo mono"
				href="https://github.com/DavidTeju/flight-statistics"
				target="_blank"
				rel="noopener noreferrer"
				aria-label="View source on GitHub"
			>
				<svg class="repo-icon" viewBox="0 0 16 16" aria-hidden="true">
					<path
						fill="currentColor"
						d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8Z"
					/>
				</svg>
				<span class="repo-label">SOURCE</span>
			</a>
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

	.repo {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 10px;
		letter-spacing: 0.2em;
		color: var(--ink);
		padding: 5px 10px 5px 8px;
		border: 1px solid var(--ink);
		border-radius: 999px;
		background: var(--bg-2);
		text-decoration: none;
		transition: background 120ms, color 120ms;
	}

	.repo:hover,
	.repo:focus-visible {
		background: var(--ink);
		color: var(--bg-2);
	}

	.repo-icon {
		width: 13px;
		height: 13px;
		display: block;
	}

	@media (max-width: 720px) {
		.repo {
			font-size: 9px;
			padding: 4px 9px 4px 7px;
		}
		.repo-label {
			display: none;
		}
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
