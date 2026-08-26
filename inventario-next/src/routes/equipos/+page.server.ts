import { searchEquipment } from '$lib/server/equipment-search';

export async function load({ url }) {
	const query = url.searchParams.get('q') ?? '';
	return searchEquipment({ query });
}
