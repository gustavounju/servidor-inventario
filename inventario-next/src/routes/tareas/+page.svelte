<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();

	const summaryCards = $derived([
		{ label: 'Tareas', value: data.summary.total },
		{ label: 'Abiertas', value: data.summary.open },
		{ label: 'Asignadas', value: data.summary.assigned },
		{ label: 'Resueltas', value: data.summary.done }
	]);

	const statuses = ['', 'Pendiente', 'Asignada', 'Hecha', 'resuelto'];

	function formatDate(value: string) {
		if (!value) return '';
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) return value;
		return new Intl.DateTimeFormat('es-AR', {
			dateStyle: 'short',
			timeStyle: 'short'
		}).format(date);
	}
</script>

<svelte:head>
	<title>Tareas - Inventario Next</title>
</svelte:head>

<main class="tasks-shell">
	<a class="back-link" href={resolve('/')}>Inventario Next</a>

	<header class="page-header">
		<div>
			<p class="eyebrow">Gestion de tareas</p>
			<h1>Tareas</h1>
			<p class="subtitle">Solicitantes enriquecidos con fuero cuando existe match de dominio.</p>
		</div>
		<div class="mode" data-mode={data.mode}>
			<span>Origen</span>
			<strong>{data.mode}</strong>
		</div>
	</header>

	<section class="summary-grid" aria-label="Resumen de tareas">
		{#each summaryCards as item (item.label)}
			<div>
				<strong>{item.value}</strong>
				<span>{item.label}</span>
			</div>
		{/each}
	</section>

	<form class="filters" method="GET" action={resolve('/tareas')}>
		<label>
			<span>Buscar</span>
			<input
				name="q"
				type="search"
				value={data.query}
				placeholder="Equipo, descripcion, solicitante"
				autocomplete="off"
			/>
		</label>
		<label>
			<span>Estado</span>
			<select name="estado" value={data.status}>
				{#each statuses as status (status || 'todos')}
					<option value={status}>{status || 'Todos'}</option>
				{/each}
			</select>
		</label>
		<button type="submit">Filtrar</button>
	</form>

	<p class="note">{data.note}</p>

	<section class="task-list" aria-label="Listado de tareas">
		{#if data.tasks.length}
			{#each data.tasks as task (task.id)}
				<article class="task-row" data-status={task.status}>
					<div class="task-main">
						<strong>{task.description}</strong>
						<span>{task.pcName} · {task.category || 'Sin categoria'}</span>
					</div>
					<div class="requester">
						<span>Solicitante</span>
						<strong>{task.requesterLabel}</strong>
						{#if task.assignedTo}
							<em>Asignada a {task.assignedTo}</em>
						{/if}
					</div>
					<div class="state">
						<strong>{task.status}</strong>
						<span>{formatDate(task.createdAt)}</span>
						{#if task.priority}
							<em>Prioridad {task.priority}</em>
						{/if}
					</div>
				</article>
			{/each}
		{:else}
			<p class="empty">No hay tareas para ese criterio.</p>
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

	.tasks-shell {
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
	.task-main span,
	.requester span,
	.requester em,
	.state span,
	.state em {
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

	.summary-grid div,
	.task-row,
	.empty {
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
	}

	.summary-grid div {
		padding: 16px;
	}

	.summary-grid strong,
	.summary-grid span,
	.task-main strong,
	.task-main span,
	.requester span,
	.requester strong,
	.requester em,
	.state strong,
	.state span,
	.state em {
		display: block;
	}

	.summary-grid strong {
		font-size: 2rem;
		line-height: 1;
	}

	.summary-grid span {
		margin-top: 8px;
	}

	.filters {
		display: grid;
		grid-template-columns: minmax(220px, 1fr) minmax(160px, 220px) auto;
		gap: 10px;
		align-items: end;
		max-width: 900px;
		margin-bottom: 14px;
	}

	.filters label span {
		display: block;
		margin-bottom: 8px;
		color: #c5d0dd;
		font-weight: 700;
	}

	.filters input,
	.filters select,
	.filters button {
		width: 100%;
		box-sizing: border-box;
		border-radius: 6px;
		font: inherit;
	}

	.filters input,
	.filters select {
		padding: 11px 12px;
		border: 1px solid #354356;
		background: #0a0e14;
		color: #eef2f7;
	}

	.filters button {
		padding: 11px 16px;
		border: 1px solid #81d8d0;
		background: #81d8d0;
		color: #071012;
		font-weight: 800;
	}

	.note {
		margin-bottom: 16px;
	}

	.task-list {
		display: grid;
		gap: 10px;
	}

	.task-row {
		display: grid;
		grid-template-columns: minmax(220px, 1.2fr) minmax(180px, 0.9fr) minmax(140px, 0.55fr);
		gap: 18px;
		padding: 14px 16px;
	}

	.task-main span,
	.requester strong,
	.requester em,
	.state span,
	.state em {
		margin-top: 4px;
	}

	.requester em,
	.state em {
		font-style: normal;
	}

	.state strong {
		color: #f5c451;
	}

	.empty {
		padding: 20px;
	}

	@media (max-width: 900px) {
		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.filters,
		.task-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 620px) {
		.tasks-shell {
			padding: 18px;
		}

		.page-header {
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
