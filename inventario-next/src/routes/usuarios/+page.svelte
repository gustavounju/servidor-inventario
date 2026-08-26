<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();

	const summaryCards = $derived([
		{ label: 'Usuarios', value: data.summary.total },
		{ label: 'Activos', value: data.summary.active },
		{ label: 'Vinculados AD', value: data.summary.linked },
		{ label: 'Solo AD', value: data.summary.adOnly }
	]);

	function sourceLabel(source: string) {
		if (source === 'linked') return 'Local + AD';
		if (source === 'ad') return 'Active Directory';
		return 'Local';
	}
</script>

<svelte:head>
	<title>Usuarios - Inventario Next</title>
</svelte:head>

<main class="users-shell">
	<a class="back-link" href={resolve('/')}>Inventario Next</a>

	<header class="page-header">
		<div>
			<p class="eyebrow">Gestion de usuarios</p>
			<h1>Usuarios</h1>
			<p class="subtitle">Lectura unificada de operadores locales y usuarios de dominio.</p>
		</div>
		<div class="mode" data-mode={data.mode}>
			<span>Origen</span>
			<strong>{data.mode}</strong>
		</div>
	</header>

	<section class="summary-grid" aria-label="Resumen de usuarios">
		{#each summaryCards as item (item.label)}
			<div>
				<strong>{item.value}</strong>
				<span>{item.label}</span>
			</div>
		{/each}
	</section>

	<form class="search" method="GET" action={resolve('/usuarios')}>
		<label for="q">Buscar por usuario, nombre, rol o fuero</label>
		<div>
			<input
				id="q"
				name="q"
				type="search"
				value={data.query}
				placeholder="Ej: gustavo, sistemas, tecnico"
				autocomplete="off"
			/>
			<button type="submit">Buscar</button>
		</div>
	</form>

	<p class="note">{data.note}</p>

	<section class="user-list" aria-label="Listado de usuarios">
		{#if data.users.length}
			{#each data.users as user (user.username)}
				<article class="user-row" data-source={user.source}>
					<div class="identity">
						<strong>{user.displayName}</strong>
						<span>{user.username}</span>
						{#if user.fuero}
							<em>{user.fuero}</em>
						{/if}
					</div>
					<div class="meta">
						<span>{sourceLabel(user.source)}</span>
						<span>{user.role}</span>
						<span>{user.isActive ? 'Activo' : 'Inactivo'}</span>
					</div>
					<div class="permissions">
						{#if user.permissions.length}
							{#each user.permissions as permission (permission)}
								<span>{permission}</span>
							{/each}
						{:else}
							<span>Sin permisos locales</span>
						{/if}
					</div>
				</article>
			{/each}
		{:else}
			<p class="empty">No hay usuarios para ese criterio.</p>
		{/if}
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		background: #0e1116;
		color: #eef2f7;
		font-family:
			Inter,
			ui-sans-serif,
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			sans-serif;
	}

	.users-shell {
		min-height: 100vh;
		box-sizing: border-box;
		padding: 28px;
		background:
			linear-gradient(90deg, rgba(24, 60, 81, 0.2) 1px, transparent 1px),
			linear-gradient(0deg, rgba(24, 60, 81, 0.18) 1px, transparent 1px), #0e1116;
		background-size: 44px 44px;
	}

	.back-link {
		color: #81d8d0;
		font-weight: 700;
		text-decoration: none;
	}

	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 24px;
		margin-top: 20px;
		padding-bottom: 22px;
		border-bottom: 1px solid #253140;
	}

	.eyebrow {
		margin: 0 0 8px;
		color: #81d8d0;
		font-size: 0.78rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	h1,
	p {
		margin: 0;
	}

	h1 {
		font-size: clamp(2rem, 6vw, 4rem);
		line-height: 1;
	}

	.subtitle,
	.note,
	.empty,
	.mode span,
	.summary-grid span,
	.identity span,
	.meta span,
	.permissions span {
		color: #9aa8b8;
	}

	.subtitle {
		margin-top: 10px;
	}

	.mode {
		display: grid;
		gap: 4px;
		min-width: 140px;
		padding: 12px 14px;
		border: 1px solid #354356;
		background: rgba(10, 14, 20, 0.82);
		border-radius: 6px;
		text-align: right;
	}

	.mode strong {
		text-transform: uppercase;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 12px;
		margin: 22px 0;
	}

	.summary-grid div {
		padding: 16px;
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
	}

	.summary-grid strong,
	.summary-grid span {
		display: block;
	}

	.summary-grid strong {
		font-size: 2rem;
		line-height: 1;
	}

	.summary-grid span {
		margin-top: 8px;
	}

	.search {
		max-width: 760px;
		margin-bottom: 14px;
	}

	.search label {
		display: block;
		margin-bottom: 8px;
		color: #c5d0dd;
		font-weight: 700;
	}

	.search div {
		display: flex;
		gap: 10px;
	}

	.search input,
	.search button {
		border-radius: 6px;
		font: inherit;
	}

	.search input {
		flex: 1;
		min-width: 0;
		padding: 11px 12px;
		border: 1px solid #354356;
		background: #0a0e14;
		color: #eef2f7;
	}

	.search button {
		padding: 11px 16px;
		border: 1px solid #81d8d0;
		background: #81d8d0;
		color: #071012;
		font-weight: 800;
	}

	.note {
		margin-bottom: 16px;
	}

	.user-list {
		display: grid;
		gap: 10px;
	}

	.user-row {
		display: grid;
		grid-template-columns: minmax(180px, 0.9fr) minmax(180px, 0.75fr) minmax(0, 1.2fr);
		gap: 18px;
		padding: 14px 16px;
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
	}

	.identity strong,
	.identity span,
	.identity em,
	.meta span {
		display: block;
	}

	.identity span,
	.identity em,
	.meta span + span {
		margin-top: 4px;
	}

	.identity em {
		color: #f5c451;
		font-style: normal;
	}

	.permissions {
		display: flex;
		flex-wrap: wrap;
		align-content: start;
		gap: 6px;
	}

	.permissions span {
		padding: 4px 7px;
		border: 1px solid #354356;
		border-radius: 999px;
		font-size: 0.78rem;
	}

	.empty {
		padding: 20px;
		border: 1px solid #253140;
		border-radius: 6px;
		background: rgba(16, 22, 30, 0.94);
	}

	@media (max-width: 900px) {
		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.user-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 620px) {
		.users-shell {
			padding: 18px;
		}

		.page-header,
		.search div {
			display: grid;
		}

		.summary-grid {
			grid-template-columns: 1fr;
		}

		.mode {
			width: fit-content;
			text-align: left;
		}
	}
</style>
