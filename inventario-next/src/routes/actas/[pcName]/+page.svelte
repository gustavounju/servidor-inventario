<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();

	const generatedAt = $derived(formatDate(data.generatedAt));

	function formatDate(value: string) {
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) return value;
		return new Intl.DateTimeFormat('es-AR', {
			dateStyle: 'long',
			timeStyle: 'short'
		}).format(date);
	}
</script>

<svelte:head>
	<title>{data.actNumber} - Inventario Next</title>
</svelte:head>

<main class="act-page">
	<nav class="toolbar" aria-label="Acciones del acta">
		<a href={resolve('/actas')}>Actas</a>
		<a href={resolve(`/equipos/${encodeURIComponent(data.pcName)}`)}>Detalle de equipo</a>
		<button type="button" onclick={() => window.print()}>Imprimir / PDF</button>
	</nav>

	<section class="sheet" aria-label="Acta de entrega">
		<header class="act-header">
			<div>
				<p>Poder Judicial de Jujuy</p>
				<h1>Acta de entrega de equipamiento</h1>
			</div>
			<div>
				<strong>{data.actNumber}</strong>
				<span>{generatedAt}</span>
			</div>
		</header>

		<section class="identity-grid" aria-label="Datos principales">
			<div>
				<span>Equipo</span>
				<strong>{data.pcName}</strong>
			</div>
			<div>
				<span>Recibe</span>
				<strong>{data.recipientName}</strong>
			</div>
			<div>
				<span>Fuero / dependencia</span>
				<strong>{data.recipientFuero}</strong>
			</div>
			<div>
				<span>Origen</span>
				<strong>{data.mode}</strong>
			</div>
		</section>

		<section class="system-grid" aria-label="Datos del sistema">
			<div>
				<span>Sistema</span>
				<strong>{data.system.osName || 'Sin dato'}</strong>
			</div>
			<div>
				<span>IP</span>
				<strong>{data.system.ipAddress || 'Sin dato'}</strong>
			</div>
			<div>
				<span>Procesador</span>
				<strong>{data.system.processor || 'Sin dato'}</strong>
			</div>
			<div>
				<span>RAM</span>
				<strong>{data.system.ramGb || 'Sin dato'}</strong>
			</div>
			<div>
				<span>Office</span>
				<strong>{data.system.officeVersion || 'Sin dato'}</strong>
			</div>
		</section>

		<section class="items" aria-label="Componentes entregados">
			<h2>Componentes incluidos en el acta</h2>
			<table>
				<thead>
					<tr>
						<th>#</th>
						<th>Tipo</th>
						<th>Descripcion</th>
						<th>Serie</th>
						<th>Estado</th>
					</tr>
				</thead>
				<tbody>
					{#each data.items as item (item.index)}
						<tr data-status={item.status}>
							<td>{item.index}</td>
							<td>{item.family}</td>
							<td>{item.description}</td>
							<td>{item.serialNumber}</td>
							<td>{item.status === 'ok' ? 'Coincide' : 'Revisar'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</section>

		<section class="review" aria-label="Alertas del acta">
			<h2>{data.reviewRequired ? 'Revision requerida' : 'Control de discrepancias'}</h2>
			{#if data.discrepancies.length}
				<ul>
					{#each data.discrepancies as item (item.message)}
						<li>
							<strong>{item.message}</strong>
							<span>{item.recommendedAction}</span>
						</li>
					{/each}
				</ul>
			{:else}
				<p>Sin discrepancias detectadas.</p>
			{/if}
		</section>

		<section class="signatures" aria-label="Firmas">
			<div>
				<span>Entrega</span>
			</div>
			<div>
				<span>Recibe conforme</span>
			</div>
			<div>
				<span>Aclaracion / DNI</span>
			</div>
		</section>

		<p class="note">{data.note}</p>
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		background: #0e1116;
		color: #101820;
		font-family:
			Inter,
			ui-sans-serif,
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			sans-serif;
	}

	.act-page {
		min-height: 100vh;
		padding: 22px;
		box-sizing: border-box;
		background: #0e1116;
	}

	.toolbar {
		display: flex;
		gap: 10px;
		align-items: center;
		max-width: 1060px;
		margin: 0 auto 14px;
	}

	.toolbar a,
	.toolbar button {
		padding: 9px 12px;
		border: 1px solid #354356;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
		color: #eef2f7;
		font: inherit;
		font-weight: 750;
		text-decoration: none;
	}

	.toolbar button {
		margin-left: auto;
		border-color: #81d8d0;
		background: #81d8d0;
		color: #071012;
		cursor: pointer;
	}

	.sheet {
		max-width: 1060px;
		margin: 0 auto;
		padding: 34px;
		background: #ffffff;
		border-radius: 6px;
		box-shadow: 0 20px 80px rgba(0, 0, 0, 0.3);
	}

	.act-header {
		display: flex;
		justify-content: space-between;
		gap: 24px;
		padding-bottom: 18px;
		border-bottom: 2px solid #101820;
	}

	h1,
	h2,
	p {
		margin: 0;
	}

	.act-header p,
	.identity-grid span,
	.system-grid span,
	.note {
		color: #52606d;
	}

	h1 {
		margin-top: 5px;
		font-size: 1.55rem;
	}

	.act-header strong,
	.act-header span {
		display: block;
		text-align: right;
	}

	.act-header span {
		margin-top: 6px;
		color: #52606d;
	}

	.identity-grid,
	.system-grid {
		display: grid;
		gap: 10px;
		margin-top: 18px;
	}

	.identity-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.system-grid {
		grid-template-columns: repeat(5, minmax(0, 1fr));
	}

	.identity-grid div,
	.system-grid div {
		min-width: 0;
		padding: 11px;
		border: 1px solid #d9e0e7;
		border-radius: 4px;
	}

	.identity-grid span,
	.identity-grid strong,
	.system-grid span,
	.system-grid strong {
		display: block;
		overflow-wrap: anywhere;
	}

	.identity-grid strong,
	.system-grid strong {
		margin-top: 4px;
	}

	.items,
	.review,
	.signatures {
		margin-top: 24px;
	}

	h2 {
		margin-bottom: 10px;
		font-size: 1rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 9px;
		border: 1px solid #d9e0e7;
		text-align: left;
		vertical-align: top;
	}

	th {
		background: #edf2f7;
		font-size: 0.8rem;
		text-transform: uppercase;
	}

	tr[data-status='review'] td {
		background: #fff8e6;
	}

	.review {
		padding: 14px;
		border: 1px solid #d9e0e7;
		border-radius: 4px;
	}

	.review ul {
		margin: 0;
		padding-left: 18px;
	}

	.review li + li {
		margin-top: 8px;
	}

	.review strong,
	.review span {
		display: block;
	}

	.review span {
		margin-top: 3px;
		color: #52606d;
	}

	.signatures {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 18px;
		padding-top: 42px;
	}

	.signatures div {
		border-top: 1px solid #101820;
		text-align: center;
	}

	.signatures span {
		display: block;
		margin-top: 8px;
	}

	.note {
		margin-top: 18px;
		font-size: 0.82rem;
	}

	@media (max-width: 860px) {
		.identity-grid,
		.system-grid,
		.signatures {
			grid-template-columns: 1fr;
		}

		.act-header,
		.toolbar {
			display: grid;
		}

		.toolbar button {
			margin-left: 0;
		}
	}

	@media print {
		:global(body),
		.act-page {
			background: #ffffff;
		}

		.act-page {
			padding: 0;
		}

		.toolbar {
			display: none;
		}

		.sheet {
			max-width: none;
			padding: 0;
			box-shadow: none;
			border-radius: 0;
		}
	}
</style>
