import { describe, expect, it } from 'vitest';
import { completeLoginAttempt, resetLoginRateLimit, startLoginAttempt } from './login-rate-limit';

describe('login rate limit', () => {
	it('rejects a second login while the same user and client are already authenticating', () => {
		resetLoginRateLimit();
		const first = startLoginAttempt('10.0.0.8', 'gmurad', 1000);
		const second = startLoginAttempt('10.0.0.8', 'gmurad', 1001);

		expect(first.allowed).toBe(true);
		expect(second).toMatchObject({
			allowed: false,
			error: 'Ya hay un intento de ingreso en curso. Esperá unos segundos.'
		});
	});

	it('allows a new attempt after the in-flight login completes', () => {
		resetLoginRateLimit();
		const first = startLoginAttempt('10.0.0.8', 'gmurad', 1000);
		completeLoginAttempt(first, false, 1001);

		expect(startLoginAttempt('10.0.0.8', 'gmurad', 1002).allowed).toBe(true);
	});

	it('expires an abandoned in-flight login guard', () => {
		resetLoginRateLimit();
		startLoginAttempt('10.0.0.8', 'gmurad', 1000);

		expect(startLoginAttempt('10.0.0.8', 'gmurad', 31_001).allowed).toBe(true);
	});

	it('temporarily blocks repeated failed attempts before another AD bind can run', () => {
		resetLoginRateLimit();

		for (let attempt = 0; attempt < 5; attempt += 1) {
			const ticket = startLoginAttempt('10.0.0.8', 'gmurad', 1000 + attempt);
			expect(ticket.allowed).toBe(true);
			completeLoginAttempt(ticket, false, 1000 + attempt);
		}

		expect(startLoginAttempt('10.0.0.8', 'gmurad', 1010)).toMatchObject({
			allowed: false,
			error: 'Demasiados intentos fallidos. Probá de nuevo en 5 minutos.',
			status: 429
		});
	});

	it('does not block the same username from a different client address', () => {
		resetLoginRateLimit();

		for (let attempt = 0; attempt < 5; attempt += 1) {
			const ticket = startLoginAttempt('10.0.0.8', 'gmurad', 1000 + attempt);
			completeLoginAttempt(ticket, false, 1000 + attempt);
		}

		expect(startLoginAttempt('10.0.0.9', 'gmurad', 1010).allowed).toBe(true);
	});

	it('clears failed-attempt history after a successful login', () => {
		resetLoginRateLimit();

		for (let attempt = 0; attempt < 4; attempt += 1) {
			const ticket = startLoginAttempt('10.0.0.8', 'gmurad', 1000 + attempt);
			completeLoginAttempt(ticket, false, 1000 + attempt);
		}

		const success = startLoginAttempt('10.0.0.8', 'gmurad', 1010);
		completeLoginAttempt(success, true, 1011);

		expect(startLoginAttempt('10.0.0.8', 'gmurad', 1012).allowed).toBe(true);
	});
});
