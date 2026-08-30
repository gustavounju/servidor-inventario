package ar.gob.justicia.sanpedro.inventario.login;

import java.util.List;

import ar.gob.justicia.sanpedro.inventario.modules.ModuleCatalogService;
import ar.gob.justicia.sanpedro.inventario.modules.ModuleDefinition;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
public class LoginController {

	public static final String AUTH_SESSION_KEY = "INVENTARIO_MODULAR_USER";

	private final LocalAuthenticationService authenticationService;
	private final ModuleCatalogService moduleCatalogService;

	LoginController(LocalAuthenticationService authenticationService, ModuleCatalogService moduleCatalogService) {
		this.authenticationService = authenticationService;
		this.moduleCatalogService = moduleCatalogService;
	}

	@GetMapping("/")
	String index() {
		return "redirect:/login";
	}

	@GetMapping(value = "/login", produces = MediaType.TEXT_HTML_VALUE)
	@ResponseBody
	String login(HttpSession session) {
		if (session.getAttribute(AUTH_SESSION_KEY) instanceof AuthenticatedUser) {
			return """
					<!doctype html>
					<html lang="es">
					<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url=/app"><title>Inventario Modular</title></head>
					<body><a href="/app">Entrar al Inventario Modular</a></body>
					</html>
					""";
		}

		return loginPage(null);
	}

	@PostMapping(value = "/login", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE, produces = MediaType.TEXT_HTML_VALUE)
	@ResponseBody
	String authenticate(
			@RequestParam(defaultValue = "") String username,
			@RequestParam(defaultValue = "") String password,
			@RequestParam(defaultValue = "local") String authMode,
			HttpServletRequest request) {
		AuthenticationResult result = authenticationService.authenticate(username, password, authMode);
		if (!result.success()) {
			return loginPage(result.message());
		}

		request.getSession(true).setAttribute(AUTH_SESSION_KEY, result.user());
		return """
				<!doctype html>
				<html lang="es">
				<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url=/app"><title>Inventario Modular</title></head>
				<body><a href="/app">Entrar al Inventario Modular</a></body>
				</html>
				""";
	}

	@PostMapping("/logout")
	String logout(HttpServletRequest request) {
		request.getSession().invalidate();
		return "redirect:/login";
	}

	@GetMapping(value = "/app", produces = MediaType.TEXT_HTML_VALUE)
	@ResponseBody
	String app(HttpSession session) {
		Object currentUser = session.getAttribute(AUTH_SESSION_KEY);
		if (!(currentUser instanceof AuthenticatedUser user)) {
			return """
					<!doctype html>
					<html lang="es">
					<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url=/login"><title>Inventario Modular</title></head>
					<body><a href="/login">Volver al login</a></body>
					</html>
					""";
		}

		List<ModuleDefinition> modules = moduleCatalogService.listModules();
		StringBuilder moduleItems = new StringBuilder();
		for (ModuleDefinition module : modules) {
			moduleItems.append("<li><strong>")
					.append(escapeHtml(module.label()))
					.append("</strong><span>")
					.append(escapeHtml(module.description()))
					.append("</span></li>");
		}

		return """
				<!doctype html>
				<html lang="es">
				<head>
					<meta charset="utf-8">
					<meta name="viewport" content="width=device-width, initial-scale=1">
					<title>Inventario Modular</title>
					<style>
						__BASE_STYLES__
						body { display: block; padding: 0; }
						.app-shell { min-height: 100vh; background: var(--bg); }
						header { background: var(--panel); border-bottom: 1px solid var(--line); padding: 18px 24px; }
						.header-inner { max-width: 1040px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
						.header-title { margin: 0; font-size: 1.15rem; }
						.header-user { color: var(--muted); font-size: 0.95rem; }
						.content { max-width: 1040px; margin: 0 auto; padding: 28px 24px; }
						.module-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; padding: 0; margin: 22px 0 0; list-style: none; }
						.module-list li { border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 14px; display: grid; gap: 8px; }
						.module-list span { color: var(--muted); line-height: 1.4; }
						.logout { border: 1px solid var(--line); background: transparent; color: var(--ink); cursor: pointer; opacity: 1; }
					</style>
				</head>
				<body>
					<div class="app-shell">
						<header>
							<div class="header-inner">
								<div>
									<p class="eyebrow">Centro Judicial San Pedro</p>
									<h1 class="header-title">Inventario Modular</h1>
								</div>
								<div class="header-user">
									%s · %s
									<form method="post" action="/logout" style="display:inline; margin-left:12px;">
										<button class="logout" type="submit">Salir</button>
									</form>
								</div>
							</div>
						</header>
						<main class="content">
							<h2>Modulos disponibles</h2>
							<ul class="module-list">%s</ul>
						</main>
					</div>
				</body>
				</html>
				""".formatted(baseStyles(), escapeHtml(user.displayName()), escapeHtml(user.role()), moduleItems);
	}

	private String loginPage(String error) {
		String errorBlock = "";
		if (error != null && !error.isBlank()) {
			errorBlock = "<p class=\"error\" role=\"alert\">" + escapeHtml(error) + "</p>";
		}

		return """
				<!doctype html>
				<html lang="es">
				<head>
					<meta charset="utf-8">
					<meta name="viewport" content="width=device-width, initial-scale=1">
					<title>Inventario Modular</title>
					<style>
						%s
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
							cursor: pointer;
						}

						button:hover {
							background: var(--accent-dark);
						}

						.modes {
							display: grid;
							grid-template-columns: 1fr 1fr;
							gap: 8px;
						}

						.modes label {
							display: flex;
							align-items: center;
							gap: 8px;
							border: 1px solid var(--line);
							border-radius: 6px;
							padding: 10px;
							font-weight: 650;
						}

						.error {
							margin-top: 18px;
							padding: 12px;
							border: 1px solid #d26060;
							border-radius: 6px;
							background: #fff0f0;
							color: #7a1818;
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

						<form method="post" action="/login">
							<div class="modes" role="radiogroup" aria-label="Modo de autenticacion">
								<label><input type="radio" name="authMode" value="local" checked> Local</label>
								<label><input type="radio" name="authMode" value="domain"> Dominio</label>
							</div>

							<label for="username">
								Usuario
								<input id="username" name="username" type="text" autocomplete="username" required autofocus>
							</label>

							<label for="password">
								Contrasena
								<input id="password" name="password" type="password" autocomplete="current-password" required>
							</label>

							<button type="submit">Ingresar</button>
						</form>

						__ERROR_BLOCK__
					</main>
				</body>
				</html>
				"""
				.replace("__BASE_STYLES__", baseStyles())
				.replace("__ERROR_BLOCK__", errorBlock);
	}

	private String baseStyles() {
		return """
				:root {
					color-scheme: light;
					--bg: #f4f6f8;
					--panel: #ffffff;
					--ink: #18212f;
					--muted: #657287;
					--line: #d8dee8;
					--accent: #126a72;
					--accent-dark: #0d535a;
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

				.eyebrow {
					margin: 0 0 8px;
					color: var(--accent);
					font-size: 0.78rem;
					font-weight: 700;
					letter-spacing: 0;
					text-transform: uppercase;
				}
				""";
	}

	private String escapeHtml(String value) {
		return (value == null ? "" : value)
				.replace("&", "&amp;")
				.replace("<", "&lt;")
				.replace(">", "&gt;")
				.replace("\"", "&quot;")
				.replace("'", "&#39;");
	}
}
