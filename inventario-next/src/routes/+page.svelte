<script lang="ts">
	import { resolve } from '$app/paths';

	const modules = [
		{
			name: 'Detalle de equipo',
			state: 'Primer corte',
			metric: 'WMI + patrimonio + acta',
			href: resolve('/equipos')
		},
		{ name: 'Actas', state: 'Pendiente', metric: 'PDF desde datos reconciliados' },
		{ name: 'Dashboard', state: 'Pendiente', metric: 'Lectura MySQL controlada' },
		{ name: 'Movil tecnicos', state: 'Base lista', metric: 'PWA y certificados' }
	];
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
			<span>Paralelo</span>
			<strong>Solo sistemas</strong>
		</div>
	</section>

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
			<li>Active Directory, TLS y acceso movil quedan como requisitos de plataforma.</li>
			<li>Los modulos heredados sin uso, como mapas, no entran al nuevo frente.</li>
		</ul>
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
	.module p,
	.console span,
	.console li {
		color: #9aa8b8;
	}

	.environment strong {
		color: #f5c451;
		font-size: 0.95rem;
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
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

	@media (max-width: 900px) {
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

		.status-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
