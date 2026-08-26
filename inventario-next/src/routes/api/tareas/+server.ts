import { json } from '@sveltejs/kit';
import { loadTaskBoard } from '$lib/server/task-board';

export async function GET({ url }) {
	return json(
		await loadTaskBoard({
			query: url.searchParams.get('q') ?? '',
			status: url.searchParams.get('estado') ?? ''
		})
	);
}
