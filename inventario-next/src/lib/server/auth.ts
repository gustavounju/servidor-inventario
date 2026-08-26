import bcrypt from 'bcryptjs';
import type { Cookies } from '@sveltejs/kit';
import { appConfig } from './config';
import { getMysqlPool } from './db';
import { authenticateActiveDirectoryPassword, normalizeAdUsername } from './active-directory';
import type { RowDataPacket } from 'mysql2';
import { createHmac, createHash, timingSafeEqual, pbkdf2 as nodePbkdf2 } from 'node:crypto';
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
	username: string;
	password_hash?: string | null;
	display_name?: string | null;
	role?: string | null;
	is_superuser?: number | null;
	is_active?: number | null;
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
	const row = await loadAppUserForLogin(username);

	if (!row) {
		const adUser = await authenticateActiveDirectoryPassword(username, password);
		if (!adUser) return { ok: false, error: 'Credenciales incorrectas' };

		const adRow = await loadAppUserForLogin(adUser.username);
		if (!adRow) return { ok: false, error: 'Usuario sin acceso habilitado. Contactá a Sistemas.' };
		if (!Number(adRow.is_active ?? 1)) {
			return { ok: false, error: 'Usuario inactivo. Contactá a Sistemas.' };
		}
		return { ok: true, user: rowToSessionUser(adRow, adRow.display_name ?? adUser.displayName) };
	}

	if (!Number(row.is_active ?? 1)) {
		return { ok: false, error: 'Usuario inactivo. Contactá a Sistemas.' };
	}

	const hash = row.password_hash ?? '';
	const valid = hash ? await verifyPassword(password, hash) : false;

	if (!valid) {
		const adUser = await authenticateActiveDirectoryPassword(username, password);
		if (!adUser) return { ok: false, error: 'Credenciales incorrectas' };
	}

	// Intentar registrar last_login (solo si no es read-only)
	if (!appConfig.MYSQL_READ_ONLY) {
		try {
			const pool = getMysqlPool();
			await pool.query(`UPDATE app_users SET last_login = NOW() WHERE username = ?`, [
				row.username
			]);
		} catch {
			// No es crítico — continuar de todos modos
		}
	}

	return {
		ok: true,
		user: rowToSessionUser(row)
	};
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
