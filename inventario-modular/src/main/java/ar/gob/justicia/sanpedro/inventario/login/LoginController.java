package ar.gob.justicia.sanpedro.inventario.login;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
class LoginController {

	@GetMapping("/")
	String index() {
		return "redirect:/login";
	}

	@GetMapping(value = "/login", produces = MediaType.TEXT_HTML_VALUE)
	@ResponseBody
	String login() {
		return """
				<!doctype html>
				<html lang="es">
				<head>
					<meta charset="utf-8">
					<meta name="viewport" content="width=device-width, initial-scale=1">
					<title>Inventario Modular</title>
					<style>
						:root {
							color-scheme: light;
							--bg: #f4f6f8;
							--panel: #ffffff;
							--ink: #18212f;
							--muted: #657287;
							--line: #d8dee8;
							--accent: #126a72;
							--accent-dark: #0d535a;
							--warn-bg: #fff7e6;
							--warn-line: #e8c36a;
						}

						* {
							box-sizing: border-box;
						}

						body {
							margin: 0;
							min-height: 100vh;
							display: grid;
							place-items: center;
							padding: 24px;
							background: var(--bg);
							color: var(--ink);
							font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
						}

						main {
							width: min(100%, 420px);
							background: var(--panel);
							border: 1px solid var(--line);
							border-radius: 8px;
							padding: 28px;
							box-shadow: 0 14px 40px rgba(24, 33, 47, 0.10);
						}

						.header {
							margin-bottom: 24px;
						}

						.eyebrow {
							margin: 0 0 8px;
							color: var(--accent);
							font-size: 0.78rem;
							font-weight: 700;
							letter-spacing: 0;
							text-transform: uppercase;
						}

						h1 {
							margin: 0;
							font-size: 1.65rem;
							line-height: 1.2;
						}

						.subtitle {
							margin: 8px 0 0;
							color: var(--muted);
							line-height: 1.45;
						}

						form {
							display: grid;
							gap: 16px;
						}

						label {
							display: grid;
							gap: 6px;
							font-weight: 650;
						}

						input {
							width: 100%;
							border: 1px solid var(--line);
							border-radius: 6px;
							padding: 12px;
							font: inherit;
						}

						input:focus {
							outline: 3px solid rgba(18, 106, 114, 0.22);
							border-color: var(--accent);
						}

						button {
							border: 0;
							border-radius: 6px;
							padding: 12px 16px;
							background: var(--accent);
							color: #ffffff;
							font: inherit;
							font-weight: 700;
							cursor: not-allowed;
							opacity: 0.72;
						}

						.notice {
							margin-top: 18px;
							padding: 12px;
							border: 1px solid var(--warn-line);
							border-radius: 6px;
							background: var(--warn-bg);
							color: #5e4a12;
							font-size: 0.92rem;
							line-height: 1.4;
						}

						@media (max-width: 380px) {
							body {
								padding: 16px;
							}

							main {
								padding: 22px;
							}
						}
					</style>
				</head>
				<body>
					<main aria-labelledby="login-title">
						<section class="header">
							<p class="eyebrow">Centro Judicial San Pedro</p>
							<h1 id="login-title">Inventario Modular</h1>
							<p class="subtitle">Acceso interno para el equipo de Informatica.</p>
						</section>

						<form aria-describedby="login-status">
							<label for="username">
								Usuario
								<input id="username" name="username" type="text" autocomplete="username" disabled>
							</label>

							<label for="password">
								Contrasena
								<input id="password" name="password" type="password" autocomplete="current-password" disabled>
							</label>

							<button type="button" disabled>Ingresar</button>
						</form>

						<p id="login-status" class="notice">
							Pantalla de acceso habilitada. La autenticacion contra Active Directory queda como siguiente modulo.
						</p>
					</main>
				</body>
				</html>
				""";
	}
}
