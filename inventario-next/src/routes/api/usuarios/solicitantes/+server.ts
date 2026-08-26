import { json } from '@sveltejs/kit';
import { loadUserDirectory } from '$lib/server/user-directory';

export async function GET({ url }) {
	const directory = await loadUserDirectory({
		query: url.searchParams.get('q') ?? ''
	});

	return json({
		mode: directory.mode,
		query: directory.query,
		items: directory.requesterOptions,
		note: directory.note
	});
}
