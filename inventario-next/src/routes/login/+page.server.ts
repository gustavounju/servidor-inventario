import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { login, createSession } from '$lib/server/auth';
import { completeLoginAttempt, startLoginAttempt } from '$lib/server/login-rate-limit';

export const load: PageServerLoad = async ({ cookies, url }) => {
	// Si ya tiene sesión, redirigir al inicio
	const username = cookies.get('inventario_next_session');
	if (username) {
		redirect(303, url.searchParams.get('next') || '/');
	}
	return { next: url.searchParams.get('next') || '/' };
};

export const actions: Actions = {
	default: async ({ request, cookies, url, getClientAddress }) => {
		const form = await request.formData();
		const username = String(form.get('username') ?? '').trim();
		const password = String(form.get('password') ?? '');
		const next = String(form.get('next') ?? url.searchParams.get('next') ?? '/');

		if (!username || !password) {
			return fail(400, { error: 'Completá usuario y contraseña.', username });
		}

		const attempt = startLoginAttempt(getClientAddress(), username);
		if (!attempt.allowed) {
			return fail(attempt.status ?? 429, {
				error: attempt.error ?? 'Demasiados intentos. Probá de nuevo en unos minutos.',
				username
			});
		}

		let result;
		try {
			result = await login(username, password);
		} catch (error) {
			completeLoginAttempt(attempt, false);
			throw error;
		}
		completeLoginAttempt(attempt, result.ok);

		if (!result.ok) {
			return fail(401, { error: result.error ?? 'Credenciales incorrectas.', username });
		}

		createSession(cookies, result.user!.username);
		redirect(303, next.startsWith('/') ? next : '/');
	}
};
