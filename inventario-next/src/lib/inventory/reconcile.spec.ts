import { describe, expect, it } from 'vitest';
import { reconcileEquipment } from './reconcile';

describe('reconcileEquipment', () => {
	it('splits concatenated WMI monitors and disks by serial tags', () => {
		const detail = reconcileEquipment({
			pcName: 'JCC8SEC1600006',
			user: { name: 'Juan Perez', fuero: 'Civil' },
			telemetry: {
				monitors: 'Philips Philips 241V8 (SN: ZA1418003190) LG 19EN33 (SN: LG19123456)',
				diskModels:
					'KINGSTON SA400S37240G (224GB) [SN: 50026B7785247C4D] ST500DM002-1BD142 (466GB) [SN: Z3T4ABCDE]'
			},
			registeredComponents: []
		});

		expect(detail.monitors.map((monitor) => monitor.serialNumber)).toEqual([
			'ZA1418003190',
			'LG19123456'
		]);
		expect(detail.storage.map((disk) => disk.serialNumber)).toEqual([
			'50026B7785247C4D',
			'Z3T4ABCDE'
		]);
	});

	it('deduplicates repeated WMI entries but keeps equal models with different serials', () => {
		const detail = reconcileEquipment({
			pcName: 'JCC8SEC1600006',
			telemetry: {
				monitors:
					'Samsung LS22 (SN: MON-001) | Samsung LS22 (SN: MON-001) | Samsung LS22 (SN: MON-002)',
				diskModels:
					'KINGSTON SA400S37240G (224GB) [SN: SSD-001] | KINGSTON SA400S37240G (224GB) [SN: SSD-001] | KINGSTON SA400S37240G (224GB)'
			},
			registeredComponents: []
		});

		expect(detail.monitors.map((monitor) => monitor.serialNumber)).toEqual(['MON-001', 'MON-002']);
		expect(detail.storage.map((disk) => disk.serialNumber)).toEqual(['SSD-001']);
	});

	it('marks registered components missing from WMI as discrepancies for acta review', () => {
		const detail = reconcileEquipment({
			pcName: 'JCC8SEC1600006',
			telemetry: {
				monitors: 'Philips 241V8 (SN: ZA1418003190)',
				diskModels: 'KINGSTON SA400S37240G (224GB) [SN: SSD-001]'
			},
			registeredComponents: [
				{
					componentType: 'Monitor',
					brandModel: 'Philips 241V8',
					serialNumber: 'ZA1418003190'
				},
				{
					componentType: 'Monitor',
					brandModel: 'LG 19EN33',
					serialNumber: 'LG19123456'
				}
			]
		});

		expect(detail.discrepancies).toContainEqual({
			severity: 'warning',
			componentFamily: 'monitor',
			message: 'Componente patrimonial sin coincidencia WMI: LG 19EN33 (LG19123456)'
		});
		expect(detail.actaItems.some((item) => item.serialNumber === 'LG19123456')).toBe(true);
	});
});
