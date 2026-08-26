import { error } from '@sveltejs/kit';
import { loadDeliveryActPayload } from '$lib/server/delivery-act';

export async function load({ params }) {
	const pcName = params.pcName?.trim();
	if (!pcName) {
		error(404, 'Equipo no encontrado');
	}

	return loadDeliveryActPayload(pcName);
}
