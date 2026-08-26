import { loadUserDirectory } from '$lib/server/user-directory';

export async function load({ url }) {
	return loadUserDirectory({
		query: url.searchParams.get('q') ?? ''
	});
}
