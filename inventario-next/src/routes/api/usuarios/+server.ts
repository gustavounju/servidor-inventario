import { json } from '@sveltejs/kit';
import { loadUserDirectory } from '$lib/server/user-directory';

export async function GET({ url }) {
	return json(
		await loadUserDirectory({
			query: url.searchParams.get('q') ?? ''
		})
	);
}
