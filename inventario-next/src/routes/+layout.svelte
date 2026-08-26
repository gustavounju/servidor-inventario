<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children, data } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if data?.user}
	<header class="app-header">
		<span class="session-user">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="13"
				height="13"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				<circle cx="12" cy="8" r="4" />
				<path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
			</svg>
			{data.user.username}
		</span>
		<form method="POST" action="/logout" class="logout-form">
			<button type="submit" id="btn-logout" aria-label="Cerrar sesión">Salir</button>
		</form>
	</header>
{/if}

{@render children()}

<style>
	.app-header {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 14px;
		padding: 8px 20px;
		background: rgba(9, 13, 18, 0.97);
		border-bottom: 1px solid #1c2a38;
		font-size: 0.82rem;
	}

	.session-user {
		display: flex;
		align-items: center;
		gap: 6px;
		color: #81d8d0;
		font-weight: 600;
	}

	.logout-form {
		margin: 0;
	}

	button[type='submit'] {
		padding: 4px 12px;
		border: 1px solid #2c3e52;
		background: transparent;
		border-radius: 3px;
		color: #9aa8b8;
		font-size: 0.78rem;
		font-family: inherit;
		cursor: pointer;
		transition: border-color 0.15s, color 0.15s;
	}

	button[type='submit']:hover {
		border-color: #81d8d0;
		color: #81d8d0;
	}
</style>

