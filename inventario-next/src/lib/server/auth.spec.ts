import type { Cookies } from '@sveltejs/kit';
import { afterEach, describe, expect, it } from 'vitest';
import { appConfig } from './config';
import { createSession, demoLogin, verifyPassword } from './auth';

// Acceso a las funciones internas para tests (re-exportadas abajo en un bloque separado)
// Como sign/unsign son funciones privadas del módulo, las testamos de forma indirecta
// a través del comportamiento observable de login/session.

const originalConfig = { ...appConfig };

afterEach(() => {
	Object.assign(appConfig, originalConfig);
});

function captureCookieOptions() {
	const calls: unknown[][] = [];
	const cookies = {
		set: (...args: unknown[]) => calls.push(args)
	} as unknown as Cookies;

	createSession(cookies, 'gmurad');
	return calls[0]?.[2] as { secure?: boolean } | undefined;
}

describe('verifyPassword', () => {
	it('returns true for a matching bcrypt hash', async () => {
		// Hash bcrypt de la cadena "admin" — generado con: node -e "require('bcryptjs').hash('admin',10).then(console.log)"
		const hash = '$2b$10$VT64IvWkv7QB.TtXL/JkEuNDm9Znv0eCfswdBxABkqJCMiz.KPNx2';
		expect(await verifyPassword('admin', hash)).toBe(true);
	});

	it('returns true for a matching PBKDF2-SHA256 werkzeug hash', async () => {
		// Hash real de la BD de desarrollo (usuario: administrador, pass: tdg729tdg)
		// Formato Flask: pbkdf2_sha256$<salt>$<hexdigest>, 390000 iteraciones
		const hash =
			'pbkdf2_sha256$22d36483d15a4d9b1f2b50733b16f33d$756f73abd820a342c58de95623cbb4d26ced6abdbdc314ccf1f04914a0534c15';
		expect(await verifyPassword('tdg729tdg', hash)).toBe(true);
	});

	it('returns false for a wrong password against a PBKDF2 hash', async () => {
		const hash =
			'pbkdf2_sha256$22d36483d15a4d9b1f2b50733b16f33d$756f73abd820a342c58de95623cbb4d26ced6abdbdc314ccf1f04914a0534c15';
		expect(await verifyPassword('wrong', hash)).toBe(false);
	});

	it('returns false for a wrong password', async () => {
		const hash = '$2b$10$3euPcmQFCiblsZeEu5s7p.9MUZWg6XkIGMCuAVS7wTBL7hB6HRHuu';
		expect(await verifyPassword('wrong', hash)).toBe(false);
	});

	it('returns false for an empty hash', async () => {
		expect(await verifyPassword('any', '')).toBe(false);
	});

	it('returns false for a malformed hash without throwing', async () => {
		expect(await verifyPassword('any', 'not-a-bcrypt-hash')).toBe(false);
	});
});

describe('demoLogin', () => {
	it('accepts administrador/admin credentials', async () => {
		const result = await demoLogin('administrador', 'admin');
		expect(result.ok).toBe(true);
		expect(result.user?.username).toBe('administrador');
		expect(result.user?.isSuperuser).toBe(true);
	});

	it('rejects wrong password', async () => {
		const result = await demoLogin('administrador', 'wrong');
		expect(result.ok).toBe(false);
		expect(result.error).toBeTruthy();
		expect(result.user).toBeUndefined();
	});

	it('rejects unknown username', async () => {
		const result = await demoLogin('noexiste', 'admin');
		expect(result.ok).toBe(false);
	});

	it('never throws even with empty inputs', async () => {
		await expect(demoLogin('', '')).resolves.toMatchObject({ ok: false });
	});
});

describe('createSession', () => {
	it('marks the session cookie as secure in production', () => {
		Object.assign(appConfig, { APP_ENV: 'production' });

		expect(captureCookieOptions()?.secure).toBe(true);
	});

	it('keeps the session cookie usable for local development', () => {
		Object.assign(appConfig, { APP_ENV: 'local' });

		expect(captureCookieOptions()?.secure).toBe(false);
	});
});
