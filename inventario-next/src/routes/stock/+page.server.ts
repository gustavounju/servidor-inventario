import { loadStockBoard } from '$lib/server/stock-board';

export async function load({ url }) {
	return loadStockBoard({
		query: url.searchParams.get('q') ?? '',
		state: url.searchParams.get('estado') ?? '',
		type: url.searchParams.get('tipo') ?? ''
	});
}
