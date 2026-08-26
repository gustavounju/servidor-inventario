<script lang="ts">
	import type { ActionData, PageData } from './$types';

	let { data, form }: { data: PageData; form: ActionData } = $props();
</script>

<svelte:head>
	<title>Iniciar sesión — Inventario Next</title>
</svelte:head>

<main class="login-shell">
	<div class="login-card">
		<div class="card-header">
			<p class="eyebrow">Centro Judicial San Pedro</p>
			<h1>Inventario Next</h1>
			<p class="subtitle">Acceso restringido al personal autorizado</p>
		</div>

		{#if form?.error}
			<div class="alert-error" role="alert" aria-live="assertive">
				{form.error}
			</div>
		{/if}

		<form method="POST" class="login-form" novalidate>
			<input type="hidden" name="next" value={data.next} />

			<div class="field">
				<label for="username">Usuario</label>
				<input
					id="username"
					name="username"
					type="text"
					autocomplete="username"
					autocapitalize="off"
					spellcheck="false"
					required
					value={form?.username ?? ''}
				/>
			</div>

			<div class="field">
				<label for="password">Contraseña</label>
				<input
					id="password"
					name="password"
					type="password"
					autocomplete="current-password"
					required
				/>
			</div>

			<button type="submit" id="btn-login">Ingresar</button>
		</form>

		<p class="footer-note">Inventario · Dpto. de Informática</p>
	</div>
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

	.login-shell {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: 24px;
		box-sizing: border-box;
		background:
			linear-gradient(90deg, rgba(24, 60, 81, 0.28) 1px, transparent 1px),
			linear-gradient(0deg, rgba(24, 60, 81, 0.2) 1px, transparent 1px),
			#0e1116;
		background-size: 44px 44px;
	}

	.login-card {
		width: 100%;
		max-width: 420px;
		padding: 36px 32px 28px;
		border: 1px solid #253140;
		background: rgba(9, 13, 18, 0.97);
		border-radius: 8px;
	}

	.card-header {
		margin-bottom: 28px;
	}

	.eyebrow {
		margin: 0 0 10px;
		color: #81d8d0;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	h1 {
		margin: 0;
		font-size: 2rem;
		font-weight: 800;
		line-height: 1;
		color: #eef2f7;
	}

	.subtitle {
		margin: 10px 0 0;
		color: #6b7e93;
		font-size: 0.85rem;
	}

	.alert-error {
		padding: 10px 14px;
		margin-bottom: 18px;
		border: 1px solid #7c2d2d;
		background: rgba(120, 20, 20, 0.25);
		border-radius: 4px;
		color: #ffa8a8;
		font-size: 0.88rem;
	}

	.login-form {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	label {
		font-size: 0.78rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #9aa8b8;
	}

	input[type='text'],
	input[type='password'] {
		width: 100%;
		padding: 10px 12px;
		border: 1px solid #2c3e52;
		background: rgba(14, 20, 28, 0.9);
		border-radius: 4px;
		color: #eef2f7;
		font-size: 0.95rem;
		font-family: inherit;
		outline: none;
		box-sizing: border-box;
		transition: border-color 0.15s;
	}

	input[type='text']:focus,
	input[type='password']:focus {
		border-color: #81d8d0;
	}

	button[type='submit'] {
		margin-top: 8px;
		padding: 12px;
		border: none;
		background: #81d8d0;
		border-radius: 4px;
		color: #0a0f14;
		font-size: 0.95rem;
		font-weight: 700;
		font-family: inherit;
		cursor: pointer;
		transition:
			background 0.15s,
			transform 0.1s;
	}

	button[type='submit']:hover {
		background: #a5e5df;
	}

	button[type='submit']:active {
		transform: scale(0.98);
	}

	.footer-note {
		margin: 20px 0 0;
		text-align: center;
		color: #3d5166;
		font-size: 0.78rem;
	}
</style>
