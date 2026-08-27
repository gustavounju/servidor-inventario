import bcrypt from 'bcryptjs';
import type { Cookies } from '@sveltejs/kit';
import { appConfig } from './config';
import { getMysqlPool } from './db';
import { authenticateActiveDirectoryPassword, normalizeAdUsername } from './active-directory';
import type { ActiveDirectoryUser } from './active-directory';
import type { RowDataPacket } from 'mysql2';
import { createHmac, randomBytes, timingSafeEqual, pbkdf2 as nodePbkdf2 } from 'node:crypto';
import { promisify } from 'node:util';

const pbkdf2 = promisify(nodePbkdf2);

// ─── Tipos públicos ────────────────────────────────────────────────────────────

export interface SessionUser {
	username: string;
	displayName: string;
	role: string;
	isSuperuser: boolean;
	isActive: boolean;
}

// ─── Constantes internas ───────────────────────────────────────────────────────

const COOKIE_NAME = 'inventario_next_session';
const COOKIE_MAX_AGE = 60 * 60 * 8; // 8 horas

// ─── Firma de cookie ───────────────────────────────────────────────────────────

// Exportadas solo para tests
export function sign(payload: string): string {
	const hmac = createHmac('sha256', appConfig.AUTH_SECRET);
	hmac.update(payload);
	return `${payload}.${hmac.digest('hex')}`;
}

export function unsign(signed: string): string | null {
	const lastDot = signed.lastIndexOf('.');
	if (lastDot === -1) return null;
	const payload = signed.slice(0, lastDot);
	const expected = Buffer.from(sign(payload));
	const actual = Buffer.from(signed);
	if (expected.length !== actual.length) return null;
	try {
		if (!timingSafeEqual(expected, actual)) return null;
	} catch {
		return null;
	}
	return payload;
}

// ─── Verificación de contraseña ────────────────────────────────────────────────

/**
 * Verifica una contraseña en texto plano contra un hash.
 * Soporta bcrypt ($2b$) y PBKDF2-SHA256 (werkzeug, formato Flask).
 */
export async function verifyPassword(plain: string, hash: string): Promise<boolean> {
	if (!hash) return false;
	try {
		if (hash.startsWith('$2b$') || hash.startsWith('$2a$') || hash.startsWith('$2y$')) {
			// bcrypt
			return await bcrypt.compare(plain, hash);
		}
		if (hash.startsWith('pbkdf2_sha256$')) {
			// Formato Flask: pbkdf2_sha256$<salt>$<hexdigest>
			// 390000 iteraciones fijas (definidas en utils/auth.py Flask)
			const FLASK_PBKDF2_ITERATIONS = 390000;
			const withoutPrefix = hash.slice('pbkdf2_sha256$'.length);
			const firstDollar = withoutPrefix.indexOf('$');
			if (firstDollar === -1) return false;
			const salt = withoutPrefix.slice(0, firstDollar);
			const storedHex = withoutPrefix.slice(firstDollar + 1);
			if (!salt || !storedHex) return false;
			const derived = await pbkdf2(
				plain,
				salt,
				FLASK_PBKDF2_ITERATIONS,
				storedHex.length / 2,
				'sha256'
			);
			const storedBuf = Buffer.from(storedHex, 'hex');
			if (derived.length !== storedBuf.length) return false;
			return timingSafeEqual(derived, storedBuf);
		}
		// Fallback: bcrypt
		return await bcrypt.compare(plain, hash);
	} catch {
		return false;
	}
}

// ─── Sesión ────────────────────────────────────────────────────────────────────

export function createSession(cookies: Cookies, username: string): void {
	const payload = JSON.stringify({ u: username, t: Date.now() });
	const signed = sign(Buffer.from(payload).toString('base64'));
	cookies.set(COOKIE_NAME, signed, {
		path: '/',
		httpOnly: true,
		sameSite: 'strict',
		secure: false, // true en producción con HTTPS
		maxAge: COOKIE_MAX_AGE
	});
}

export function destroySession(cookies: Cookies): void {
	cookies.delete(COOKIE_NAME, { path: '/' });
}

export function getSessionUsername(cookies: Cookies): string | null {
	const raw = cookies.get(COOKIE_NAME);
	if (!raw) return null;
	const payload = unsign(raw);
	if (!payload) return null;
	try {
		const parsed = JSON.parse(Buffer.from(payload, 'base64').toString('utf8'));
		if (typeof parsed.u !== 'string') return null;
		return parsed.u;
	} catch {
		return null;
	}
}

// ─── Filas de base de datos ───────────────────────────────────────────────────

interface AppUserAuthRow extends RowDataPacket {
	id?: number;
	username: string;
	password_hash?: string | null;
	display_name?: string | null;
	role?: string | null;
	is_superuser?: number | null;
	is_active?: number | null;
}

interface AppSettingRow extends RowDataPacket {
	setting_value: string | null;
}

// ─── Login ─────────────────────────────────────────────────────────────────────

export interface LoginResult {
	ok: boolean;
	user?: SessionUser;
	error?: string;
}

function rowToSessionUser(
	row: AppUserAuthRow,
	displayName = row.display_name ?? row.username
): SessionUser {
	return {
		username: row.username,
		displayName,
		role: row.role ?? 'usuario',
		isSuperuser: Boolean(Number(row.is_superuser ?? 0)),
		isActive: true
	};
}

async function loadAppSetting(key: string, defaultValue = '') {
	if (!appConfig.MYSQL_PASSWORD) return defaultValue;

	try {
		const pool = getMysqlPool();
		const [rows] = await pool.query<AppSettingRow[]>(
			`SELECT setting_value
			 FROM app_settings
			 WHERE setting_key = ? AND is_active = 1
			 LIMIT 1`,
			[key]
		);
		const value = rows[0]?.setting_value;
		return value === null || value === undefined ? defaultValue : String(value).trim();
	} catch {
		return defaultValue;
	}
}

async function authMode() {
	const mode = (await loadAppSetting('AUTH_MODE', 'local')).toLowerCase();
	return mode === 'ad' || mode === 'hybrid' || mode === 'local' ? mode : 'local';
}

async function adSuperusers() {
	const raw = await loadAppSetting('AD_SUPERUSERS', '');
	return new Set(
		raw
			.split(',')
			.map((item) => normalizeAdUsername(item))
			.filter(Boolean)
	);
}

async function adAutoApprove() {
	return (await loadAppSetting('AD_AUTO_APPROVE', 'false')).toLowerCase() === 'true';
}

async function loadAppUserForLogin(username: string): Promise<AppUserAuthRow | undefined> {
	const pool = getMysqlPool();
	const normalized = normalizeAdUsername(username);
	const candidates = [...new Set([username.trim(), normalized].filter(Boolean))];

	if (candidates.length === 0) return undefined;

	const placeholders = candidates.map(() => '?').join(', ');
	const [rows] = await pool.query<AppUserAuthRow[]>(
		`SELECT username, password_hash, display_name, role, is_superuser, is_active
		 FROM app_users
		 WHERE username IN (${placeholders})
		 ORDER BY FIELD(username, ${placeholders})
		 LIMIT 1`,
		[...candidates, ...candidates]
	);

	return rows[0];
}

async function ensureAdShadowUser(
	adUser: ActiveDirectoryUser
): Promise<AppUserAuthRow | undefined> {
	const username = normalizeAdUsername(adUser.username);
	if (!username) return undefined;

	const existing = await loadAppUserForLogin(username);
	const superusers = await adSuperusers();
	const isSuperuser = superusers.has(username);
	const isActive = isSuperuser || (await adAutoApprove());
	const displayName = adUser.displayName || username;

	if (existing) {
		if (!appConfig.MYSQL_READ_ONLY) {
			try {
				await getMysqlPool().query(
					`UPDATE app_users
					 SET display_name = ?,
					     is_superuser = ?,
					     is_active = CASE WHEN ? = 1 THEN 1 ELSE is_active END,
					     updated_at = CURRENT_TIMESTAMP
					 WHERE username = ?`,
					[displayName, isSuperuser ? 1 : 0, isSuperuser ? 1 : 0, existing.username]
				);
			} catch {
				// AD already authenticated; stale local profile data must not block login.
			}
		}

		return {
			...existing,
			display_name: displayName,
			is_superuser: isSuperuser ? 1 : existing.is_superuser,
			is_active: isSuperuser ? 1 : existing.is_active
		};
	}

	if (appConfig.MYSQL_READ_ONLY) return undefined;

	const generatedHash = await bcrypt.hash(randomBytes(32).toString('base64url'), 10);
	await getMysqlPool().query(
		`INSERT INTO app_users (
			username, display_name, role, technician_name, password_hash,
			is_superuser, is_active, must_change_password,
			can_access_dashboard, can_access_mobile, can_access_infrastructure,
			can_access_reports, can_access_operadores, can_audit_racks, can_manage_stock
		)
		VALUES (?, ?, ?, NULL, ?, ?, ?, 0, ?, 1, ?, ?, ?, ?, ?)`,
		[
			username,
			displayName,
			isSuperuser ? 'administrador' : 'tecnico',
			generatedHash,
			isSuperuser ? 1 : 0,
			isActive ? 1 : 0,
			isSuperuser ? 1 : 0,
			isSuperuser ? 1 : 0,
			isSuperuser ? 1 : 0,
			isSuperuser ? 1 : 0,
			isSuperuser ? 1 : 0,
			isSuperuser ? 1 : 0
		]
	);

	return await loadAppUserForLogin(username);
}

/** Login sin base de datos — solo para desarrollo sin .env configurado. */
export async function demoLogin(username: string, password: string): Promise<LoginResult> {
	const DEMO_USER = 'administrador';
	const DEMO_PASS = 'admin';

	if (username === DEMO_USER && password === DEMO_PASS) {
		return {
			ok: true,
			user: {
				username: DEMO_USER,
				displayName: 'Administrador (Demo)',
				role: 'administrador',
				isSuperuser: true,
				isActive: true
			}
		};
	}

	return { ok: false, error: 'Credenciales incorrectas' };
}

/** Login contra la tabla app_users de MySQL. */
export async function loginWithMysql(username: string, password: string): Promise<LoginResult> {
	const normalizedUsername = normalizeAdUsername(username);
	const mode = await authMode();

	if (normalizedUsername.endsWith('_adm')) {
		return {
			ok: false,
			error:
				'Por seguridad, no se permite el ingreso con cuentas administrativas (_adm). Usá tu cuenta común de AD.'
		};
	}

	const row = await loadAppUserForLogin(normalizedUsername);

	if (row && (mode === 'local' || mode === 'hybrid')) {
		const hash = row.password_hash ?? '';
		const valid = hash ? await verifyPassword(password, hash) : false;
		if (valid) {
			if (!Number(row.is_active ?? 1)) {
				return { ok: false, error: 'Usuario inactivo. Contactá a Sistemas.' };
			}
			return { ok: true, user: rowToSessionUser(row) };
		}
	}

	if (mode === 'ad' || mode === 'hybrid') {
		const adUser = await authenticateActiveDirectoryPassword(username, password);
		if (!adUser) return { ok: false, error: 'Credenciales incorrectas' };

		const adRow = await ensureAdShadowUser(adUser);
		if (!adRow) {
			return {
				ok: false,
				error:
					'AD validó el usuario, pero Inventario Next está en modo solo lectura y no puede crear el usuario local.'
			};
		}
		if (!Number(adRow.is_active ?? 1)) {
			return {
				ok: false,
				error: 'Usuario validado por AD, pendiente de aprobación en Inventario.'
			};
		}
		return { ok: true, user: rowToSessionUser(adRow, adRow.display_name ?? adUser.displayName) };
	}

	return { ok: false, error: 'Credenciales incorrectas' };
}

/** Punto de entrada unificado: usa MySQL si hay password configurado, si no usa demo. */
export async function login(username: string, password: string): Promise<LoginResult> {
	if (!appConfig.MYSQL_PASSWORD) {
		return demoLogin(username, password);
	}
	return loginWithMysql(username, password);
}

/** Carga el usuario de la sesión actual desde la cookie (sin ir a MySQL). */
export function loadSessionUser(cookies: Cookies): string | null {
	return getSessionUsername(cookies);
}
