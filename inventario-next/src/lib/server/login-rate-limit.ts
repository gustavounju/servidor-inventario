import { normalizeAdUsername } from './active-directory';
import { appConfig } from './config';

const WINDOW_MS = 5 * 60 * 1000;
const LOCK_MS = 5 * 60 * 1000;
const IN_FLIGHT_MS = 30 * 1000;
const MAX_FAILED_ATTEMPTS = 5;
const MAX_TRACKED_KEYS = 500;

interface LoginAttemptState {
	failures: number[];
	lockedUntil: number;
	inFlightUntil: number;
	lastSeen: number;
}

export interface LoginAttemptTicket {
	allowed: boolean;
	key?: string;
	error?: string;
	status?: 429;
	retryAfterSeconds?: number;
}

const attempts = new Map<string, LoginAttemptState>();

function normalizeClient(clientAddress: string) {
	return clientAddress.trim().toLowerCase() || 'unknown-client';
}

function firstForwardedAddress(header: string | null) {
	return header
		?.split(',')
		.map((address) => address.trim())
		.find(Boolean);
}

export function loginClientAddress(request: Request, fallbackAddress: string) {
	if (!appConfig.TRUST_PROXY) return fallbackAddress;

	return (
		firstForwardedAddress(request.headers.get('x-forwarded-for')) ??
		request.headers.get('x-real-ip')?.trim() ??
		fallbackAddress
	);
}

function rateLimitKey(clientAddress: string, username: string) {
	const normalizedUsername = normalizeAdUsername(username).toLowerCase();
	return `${normalizeClient(clientAddress)}:${normalizedUsername || 'unknown-user'}`;
}

function cleanupAttempts(now: number) {
	for (const [key, state] of attempts) {
		pruneFailures(state, now);
		if (
			state.failures.length === 0 &&
			state.lockedUntil <= now &&
			state.inFlightUntil <= now &&
			now - state.lastSeen > WINDOW_MS
		) {
			attempts.delete(key);
		}
	}

	while (attempts.size > MAX_TRACKED_KEYS) {
		const oldestKey = [...attempts.entries()].sort((first, second) => {
			return first[1].lastSeen - second[1].lastSeen;
		})[0]?.[0];
		if (!oldestKey) break;
		attempts.delete(oldestKey);
	}
}

function stateFor(key: string, now: number) {
	const existing = attempts.get(key);
	if (existing) {
		existing.lastSeen = now;
		return existing;
	}

	const created: LoginAttemptState = {
		failures: [],
		lockedUntil: 0,
		inFlightUntil: 0,
		lastSeen: now
	};
	attempts.set(key, created);
	cleanupAttempts(now);
	return created;
}

function pruneFailures(state: LoginAttemptState, now: number) {
	state.failures = state.failures.filter((timestamp) => now - timestamp < WINDOW_MS);
}

export function startLoginAttempt(
	clientAddress: string,
	username: string,
	now = Date.now()
): LoginAttemptTicket {
	cleanupAttempts(now);
	const key = rateLimitKey(clientAddress, username);
	const state = stateFor(key, now);
	pruneFailures(state, now);

	if (state.lockedUntil > now) {
		return {
			allowed: false,
			error: 'Demasiados intentos fallidos. Probá de nuevo en 5 minutos.',
			status: 429,
			retryAfterSeconds: Math.ceil((state.lockedUntil - now) / 1000)
		};
	}

	if (state.inFlightUntil > now) {
		return {
			allowed: false,
			error: 'Ya hay un intento de ingreso en curso. Esperá unos segundos.',
			status: 429,
			retryAfterSeconds: 3
		};
	}

	state.inFlightUntil = now + IN_FLIGHT_MS;
	return { allowed: true, key };
}

export function completeLoginAttempt(
	ticket: LoginAttemptTicket,
	success: boolean,
	now = Date.now()
) {
	if (!ticket.allowed || !ticket.key) return;

	const state = stateFor(ticket.key, now);
	state.inFlightUntil = 0;

	if (success) {
		attempts.delete(ticket.key);
		return;
	}

	pruneFailures(state, now);
	state.failures.push(now);
	if (state.failures.length >= MAX_FAILED_ATTEMPTS) {
		state.lockedUntil = now + LOCK_MS;
		state.failures = [];
	}
}

export function resetLoginRateLimit() {
	attempts.clear();
}
