import { demoEquipmentDetail, loadEquipmentDetail } from './equipment-detail';
import type { ReconciledComponent, ReconciledEquipmentDetail } from '$lib/inventory/types';

export interface DeliveryActItem {
	index: number;
	family: string;
	description: string;
	serialNumber: string;
	source: string;
	status: 'ok' | 'review';
}

export interface DeliveryActPayload {
	actNumber: string;
	generatedAt: string;
	pcName: string;
	recipientName: string;
	recipientFuero: string;
	system: {
		osName: string;
		ipAddress: string;
		processor: string;
		ramGb: string;
		officeVersion: string;
	};
	items: DeliveryActItem[];
	discrepancies: ReconciledEquipmentDetail['discrepancies'];
	reviewRequired: boolean;
	mode: 'demo' | 'mysql' | 'not_found';
	note: string;
}

function familyLabel(family: ReconciledComponent['family']) {
	if (family === 'monitor') return 'Monitor';
	if (family === 'storage') return 'Almacenamiento';
	if (family === 'processor') return 'Procesador';
	if (family === 'memory') return 'Memoria';
	if (family === 'motherboard') return 'Placa madre';
	return 'Componente';
}

function itemStatus(item: ReconciledComponent): DeliveryActItem['status'] {
	return item.inTelemetry && item.inRegistry ? 'ok' : 'review';
}

export function createDeliveryActPayload({
	detail,
	mode = 'demo',
	note = '',
	generatedAt = new Date()
}: {
	detail: ReconciledEquipmentDetail;
	mode?: DeliveryActPayload['mode'];
	note?: string;
	generatedAt?: Date;
}): DeliveryActPayload {
	const generatedDate = generatedAt.toISOString();
	const reviewRequired = detail.discrepancies.some((item) => item.severity !== 'info');

	return {
		actNumber: `ACTA-${detail.pcName}-${generatedDate.slice(0, 10).replaceAll('-', '')}`,
		generatedAt: generatedDate,
		pcName: detail.pcName,
		recipientName: detail.user.name || 'Sin usuario asignado',
		recipientFuero: detail.user.fuero || 'Sin fuero',
		system: {
			osName: detail.system.osName ?? '',
			ipAddress: detail.system.ipAddress ?? '',
			processor: detail.system.processor ?? '',
			ramGb: detail.system.ramGb ? String(detail.system.ramGb) : '',
			officeVersion: detail.system.officeVersion ?? ''
		},
		items: detail.actaItems.map((item, index) => ({
			index: index + 1,
			family: familyLabel(item.family),
			description: item.label,
			serialNumber: item.serialNumber,
			source: item.source,
			status: itemStatus(item)
		})),
		discrepancies: detail.discrepancies,
		reviewRequired,
		mode,
		note
	};
}

export function demoDeliveryActPayload(pcName = 'demo') {
	return createDeliveryActPayload({
		detail: demoEquipmentDetail(pcName),
		generatedAt: new Date('2026-08-25T10:00:00.000Z')
	});
}

export async function loadDeliveryActPayload(pcName: string) {
	const result = await loadEquipmentDetail(pcName);
	return createDeliveryActPayload({
		detail: result.detail,
		mode: result.mode,
		note: result.note
	});
}
