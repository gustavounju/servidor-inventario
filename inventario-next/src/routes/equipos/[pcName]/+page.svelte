<script lang="ts">
	import { resolve } from '$app/paths';
	import ComponentList from '$lib/components/ComponentList.svelte';

	let { data } = $props();

	const detail = $derived(data.detail);
</script>

<svelte:head>
	<title>{detail.pcName} - Inventario Next</title>
</svelte:head>

<main class="equipment-shell">
	<a class="back-link" href={resolve('/')}>Inventario Next</a>

	<header class="page-header">
		<div>
			<p class="eyebrow">Detalle reconciliado</p>
			<h1>{detail.pcName}</h1>
			<p class="owner">
				{detail.user.name || 'Sin usuario'}
				{#if detail.user.fuero}
					<span>{detail.user.fuero}</span>
				{/if}
			</p>
		</div>
		<div class="mode" data-mode={data.mode}>
			<span>Origen</span>
			<strong>{data.mode}</strong>
		</div>
	</header>

	<p class="note">{data.note}</p>

	<section class="summary-grid" aria-label="Resumen patrimonial">
		<div>
			<span>{detail.monitors.length}</span>
			<p>Monitores para acta</p>
		</div>
		<div>
			<span>{detail.storage.length}</span>
			<p>Discos para acta</p>
		</div>
		<div>
			<span>{detail.discrepancies.length}</span>
			<p>Discrepancias</p>
		</div>
	</section>

	<section class="columns">
		<div class="panel">
			<h2>Monitores</h2>
			<ComponentList items={detail.monitors} />
		</div>

		<div class="panel">
			<h2>Almacenamiento</h2>
			<ComponentList items={detail.storage} />
		</div>
	</section>

	<section class="panel">
		<h2>Alertas para revisar antes del acta</h2>
		{#if detail.discrepancies.length}
			<ul class="alerts">
				{#each detail.discrepancies as item (item.message)}
					<li>{item.message}</li>
				{/each}
			</ul>
		{:else}
			<p class="empty">Sin discrepancias detectadas en este corte.</p>
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

	.equipment-shell {
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
	h2,
	p {
		margin: 0;
	}

	h1 {
		font-size: clamp(2rem, 6vw, 4rem);
		line-height: 1;
	}

	.owner {
		margin-top: 10px;
		color: #a9b7c8;
	}

	.owner span {
		margin-left: 10px;
		color: #f5c451;
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

	.mode span,
	.note,
	.empty {
		color: #9aa8b8;
	}

	.mode strong {
		text-transform: uppercase;
	}

	.note {
		margin-top: 16px;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 12px;
		margin: 22px 0;
	}

	.summary-grid div,
	.panel {
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
	}

	.summary-grid div {
		padding: 16px;
	}

	.summary-grid span {
		display: block;
		color: #eef2f7;
		font-size: 2rem;
		font-weight: 800;
	}

	.summary-grid p {
		margin-top: 4px;
		color: #a9b7c8;
	}

	.columns {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 12px;
		margin-bottom: 12px;
	}

	.panel {
		padding: 16px;
	}

	.panel h2 {
		margin-bottom: 14px;
		font-size: 1rem;
	}

	.alerts {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.alerts li {
		padding: 10px 0;
		border-top: 1px solid #3a3140;
		color: #ffd2a1;
	}

	@media (max-width: 760px) {
		.equipment-shell {
			padding: 18px;
		}

		.page-header,
		.columns {
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
