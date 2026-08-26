import { describe, expect, it } from 'vitest';
import { createDeliveryActPayload, demoDeliveryActPayload } from './delivery-act';
import { reconcileEquipment } from '$lib/inventory/reconcile';

describe('delivery-act', () => {
	it('builds a printable act payload from reconciled equipment details', () => {
		const act = demoDeliveryActPayload('demo');

		expect(act.actNumber).toBe('ACTA-demo-20260825');
		expect(act.pcName).toBe('demo');
		expect(act.recipientName).toBe('Demo Sistemas');
		expect(act.items.length).toBeGreaterThan(1);
		expect(act.items.some((item) => item.family === 'Monitor')).toBe(true);
	});

	it('marks act review when registered patrimony is missing from telemetry', () => {
		const detail = reconcileEquipment({
			pcName: 'JCC1-PC01',
			user: { name: 'Andrea Gomez', fuero: 'Civil' },
			telemetry: {
				monitors: 'Philips 241V8 (SN: MON-001)',
				diskModels: ''
			},
			registeredComponents: [
				{
					componentType: 'Monitor',
					brandModel: 'LG 19EN33',
					serialNumber: 'MON-002'
				}
			]
		});

		const act = createDeliveryActPayload({
			detail,
			generatedAt: new Date('2026-08-25T10:00:00.000Z')
		});

		expect(act.reviewRequired).toBe(true);
		expect(act.discrepancies).toContainEqual(
			expect.objectContaining({ code: 'registered_missing_in_telemetry' })
		);
		expect(act.items.some((item) => item.serialNumber === 'MON-002')).toBe(true);
	});
});
