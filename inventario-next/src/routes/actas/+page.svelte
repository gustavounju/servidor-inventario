<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();
</script>

<svelte:head>
	<title>Actas - Inventario Next</title>
</svelte:head>

<main class="acts-shell">
	<a class="back-link" href={resolve('/')}>Inventario Next</a>

	<header class="page-header">
		<div>
			<p class="eyebrow">Actas de entrega</p>
			<h1>Actas</h1>
			<p class="subtitle">Seleccione un equipo para generar el acta imprimible reconciliada.</p>
		</div>
		<div class="mode" data-mode={data.mode}>
			<span>Origen</span>
			<strong>{data.mode}</strong>
		</div>
	</header>

	<form class="search" method="GET" action={resolve('/actas')}>
		<label for="q">Buscar equipo, usuario o fuero</label>
		<div>
			<input
				id="q"
				name="q"
				type="search"
				value={data.query}
				placeholder="Ej: DESKTOP, JCC1, Gustavo"
				autocomplete="off"
			/>
			<button type="submit">Buscar</button>
		</div>
	</form>

	<p class="note">{data.note}</p>

	<section class="acts-list" aria-label="Equipos para actas">
		{#if data.items.length}
			{#each data.items as item (item.pcName)}
				<a class="act-row" href={resolve(`/actas/${encodeURIComponent(item.pcName)}`)}>
					<div>
						<strong>{item.pcName}</strong>
						<span>{item.userName} · {item.fuero}</span>
					</div>
					<div>
						<span>{item.monitorSummary}</span>
						<span>{item.storageSummary}</span>
					</div>
					<em>Preparar acta</em>
				</a>
			{/each}
		{:else}
			<p class="empty">No hay equipos para ese criterio.</p>
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

	.acts-shell {
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
	.act-row span {
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

	.search {
		max-width: 760px;
		margin: 22px 0 14px;
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

	.acts-list {
		display: grid;
		gap: 10px;
	}

	.act-row {
		display: grid;
		grid-template-columns: minmax(180px, 0.85fr) minmax(0, 1.15fr) auto;
		gap: 18px;
		align-items: center;
		padding: 14px 16px;
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
		color: inherit;
		text-decoration: none;
	}

	.act-row:hover,
	.act-row:focus-visible {
		border-color: #81d8d0;
		outline: none;
	}

	.act-row strong,
	.act-row span {
		display: block;
	}

	.act-row span + span {
		margin-top: 4px;
	}

	.act-row em {
		color: #f5c451;
		font-style: normal;
		font-weight: 800;
	}

	.empty {
		padding: 20px;
		border: 1px solid #253140;
		border-radius: 6px;
		background: rgba(16, 22, 30, 0.94);
	}

	@media (max-width: 760px) {
		.acts-shell {
			padding: 18px;
		}

		.page-header,
		.act-row,
		.search div {
			display: grid;
		}

		.mode {
			width: fit-content;
			text-align: left;
		}
	}
</style>
