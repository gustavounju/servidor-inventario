import { searchEquipment } from '$lib/server/equipment-search';

export async function load({ url }) {
	return searchEquipment({
		query: url.searchParams.get('q') ?? '',
		limit: 40
	});
}
