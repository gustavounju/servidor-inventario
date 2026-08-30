<script lang="ts">
	import { resolve } from '$app/paths';

	let { data } = $props();

	const modules = [
		{
			name: 'Detalle de equipo',
			state: 'Primer corte',
			metric: 'WMI + patrimonio + acta',
			href: resolve('/equipos')
		},
		{
			name: 'Actas',
			state: 'Primer corte',
			metric: 'Vista imprimible desde datos reconciliados',
			href: resolve('/actas')
		},
		{
			name: 'Tareas',
			state: 'Primer corte',
			metric: 'Solicitantes con fuero',
			href: resolve('/tareas')
		},
		{ name: 'Dashboard', state: 'Pendiente', metric: 'Lectura MySQL controlada' },
		{
			name: 'Usuarios',
			state: 'Primer corte',
			metric: 'Locales + Active Directory + permisos',
			href: resolve('/usuarios')
		},
		{ name: 'Movil tecnicos', state: 'Base lista', metric: 'PWA y certificados' }
	];

	const metrics = $derived([
		{ label: 'PCs activas', value: data.metrics.activePcs },
		{ label: 'Componentes asignados', value: data.metrics.assignedComponents },
		{ label: 'Tareas abiertas', value: data.metrics.openTasks },
		{ label: 'Usuarios activos', value: data.metrics.activeUsers }
	]);
</script>

<svelte:head>
	<title>Inventario Next</title>
	<meta
		name="description"
		content="Inventario Next para el Departamento de Informatica del Centro Judicial San Pedro"
	/>
</svelte:head>

<main class="shell">
	<section class="topbar" aria-label="Estado general">
		<div>
			<p class="eyebrow">Centro Judicial San Pedro</p>
			<h1>Inventario Next</h1>
		</div>
		<div class="environment">
			<span>Origen</span>
			<strong>{data.mode}</strong>
		</div>
	</section>

	<section class="metric-grid" aria-label="Resumen operativo">
		{#each metrics as metric (metric.label)}
			<div class="metric">
				<strong>{metric.value}</strong>
				<span>{metric.label}</span>
			</div>
		{/each}
	</section>

	{#if data.todayEfemerides.length}
		<section class="efemerides" aria-label="Efemerides del dia">
			{#each data.todayEfemerides as item (item.title)}
				<article>
					<span>{item.icon}</span>
					<div>
						<h2>{item.title}</h2>
						<p>{item.description}</p>
					</div>
				</article>
			{/each}
		</section>
	{/if}

	<section class="status-grid" aria-label="Modulos iniciales">
		{#each modules as module (module.name)}
			<svelte:element this={module.href ? 'a' : 'article'} class="module" href={module.href}>
				<div>
					<h2>{module.name}</h2>
					<p>{module.metric}</p>
				</div>
				<span>{module.state}</span>
			</svelte:element>
		{/each}
	</section>

	<section class="console" aria-label="Contrato de convivencia">
		<div class="console-header">
			<h2>Contrato inicial</h2>
			<span>v0</span>
		</div>
		<ul>
			<li>Flask sigue como produccion estable.</li>
			<li>Next empieza leyendo MySQL con escritura deshabilitada por configuracion.</li>
			<li>Equipos, usuarios, tareas y actas ya tienen primer flujo navegable.</li>
			<li>Active Directory, TLS y acceso movil siguen como requisitos de plataforma.</li>
		</ul>
	</section>

	<p class="note">{data.note}</p>
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

	.shell {
		min-height: 100vh;
		box-sizing: border-box;
		padding: 28px;
		background:
			linear-gradient(90deg, rgba(24, 60, 81, 0.28) 1px, transparent 1px),
			linear-gradient(0deg, rgba(24, 60, 81, 0.2) 1px, transparent 1px), #0e1116;
		background-size: 44px 44px;
	}

	.topbar {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 24px;
		padding-bottom: 24px;
		border-bottom: 1px solid #253140;
	}

	.eyebrow {
		margin: 0 0 8px;
		color: #81d8d0;
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0;
		text-transform: uppercase;
	}

	h1,
	h2,
	p {
		margin: 0;
	}

	h1 {
		font-size: clamp(2rem, 5vw, 4.5rem);
		line-height: 0.95;
		font-weight: 800;
	}

	.environment {
		display: grid;
		gap: 4px;
		min-width: 150px;
		padding: 12px 14px;
		border: 1px solid #354356;
		background: rgba(10, 14, 20, 0.82);
		border-radius: 6px;
		text-align: right;
	}

	.environment span,
	.metric span,
	.module p,
	.console span,
	.console li,
	.note {
		color: #9aa8b8;
	}

	.environment strong {
		color: #f5c451;
		font-size: 0.95rem;
		text-transform: uppercase;
	}

	.metric-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 12px;
		margin: 24px 0 0;
	}

	.metric {
		padding: 16px;
		border: 1px solid #253140;
		background: rgba(9, 13, 18, 0.96);
		border-radius: 6px;
	}

	.metric strong,
	.metric span {
		display: block;
	}

	.metric strong {
		color: #eef2f7;
		font-size: 2rem;
		line-height: 1;
	}

	.metric span {
		margin-top: 8px;
	}

	.efemerides {
		margin-top: 12px;
	}

	.efemerides article {
		display: flex;
		gap: 12px;
		padding: 14px 16px;
		border: 1px solid #314252;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
	}

	.efemerides article > span {
		font-size: 1.4rem;
	}

	.efemerides p {
		margin-top: 4px;
		color: #a9b7c8;
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 12px;
		margin: 24px 0;
	}

	.module {
		display: grid;
		align-content: space-between;
		min-height: 132px;
		padding: 16px;
		border: 1px solid #253140;
		background: rgba(16, 22, 30, 0.94);
		border-radius: 6px;
		color: inherit;
		text-decoration: none;
	}

	a.module:hover,
	a.module:focus-visible {
		border-color: #81d8d0;
		outline: none;
	}

	.module h2,
	.console h2 {
		font-size: 1rem;
		font-weight: 750;
	}

	.module p {
		margin-top: 8px;
		font-size: 0.9rem;
		line-height: 1.45;
	}

	.module span {
		width: fit-content;
		margin-top: 18px;
		padding: 5px 8px;
		border: 1px solid #3a4a5e;
		border-radius: 999px;
		color: #c5d0dd;
		font-size: 0.78rem;
	}

	.console {
		max-width: 860px;
		border: 1px solid #253140;
		background: rgba(9, 13, 18, 0.96);
		border-radius: 6px;
	}

	.console-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 16px;
		border-bottom: 1px solid #253140;
	}

	.console ul {
		margin: 0;
		padding: 16px 16px 18px 34px;
	}

	.console li + li {
		margin-top: 10px;
	}

	.note {
		margin-top: 12px;
	}

	@media (max-width: 900px) {
		.metric-grid,
		.status-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 620px) {
		.shell {
			padding: 18px;
		}

		.topbar {
			display: grid;
		}

		.environment {
			width: fit-content;
			text-align: left;
		}

		.metric-grid,
		.status-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
