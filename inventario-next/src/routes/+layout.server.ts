import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { loadSessionUser } from '$lib/server/auth';

// Rutas que no requieren autenticación
const PUBLIC_PATHS = new Set(['/login']);

export const load: LayoutServerLoad = async ({ cookies, url }) => {
	const pathname = url.pathname;

	// Rutas públicas — pasar sin verificar
	if (PUBLIC_PATHS.has(pathname)) {
		return { user: null };
	}

	const username = loadSessionUser(cookies);

	if (!username) {
		const next = pathname !== '/' ? `?next=${encodeURIComponent(pathname)}` : '';
		redirect(303, `/login${next}`);
	}

	return {
		user: { username }
	};
};
