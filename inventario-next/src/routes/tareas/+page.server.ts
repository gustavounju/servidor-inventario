import { loadTaskBoard } from '$lib/server/task-board';

export async function load({ url }) {
	return loadTaskBoard({
		query: url.searchParams.get('q') ?? '',
		status: url.searchParams.get('estado') ?? ''
	});
}
