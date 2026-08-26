import { json, error } from '@sveltejs/kit';
import { loadEquipmentDetail } from '$lib/server/equipment-detail';

export async function GET({ params }) {
	const pcName = params.pcName?.trim();
	if (!pcName) {
		error(404, 'Equipo no encontrado');
	}

	return json(await loadEquipmentDetail(pcName));
}
