import { describe, expect, it } from 'vitest';
import { demoStockBoard, stockStateForComponent } from './stock-board';

describe('stock-board', () => {
	it('classifies stock components by lifecycle and assignment state', () => {
		expect(
			stockStateForComponent({
				status: 'Stock',
				lifecycleStatus: 'stock',
				assignedPc: '',
				assignedUser: '',
				assignedFuero: '',
				buildOrderId: null
			})
		).toBe('disponible');

		expect(
			stockStateForComponent({
				status: 'Reservado',
				lifecycleStatus: 'en_armado',
				assignedPc: '',
				assignedUser: '',
				assignedFuero: '',
				buildOrderId: 8
			})
		).toBe('reservado');

		expect(
			stockStateForComponent({
				status: 'Installed',
				lifecycleStatus: 'desplegado',
				assignedPc: 'JCC1-PC01',
				assignedUser: '',
				assignedFuero: 'Sistemas',
				buildOrderId: null
			})
		).toBe('asignado');

		expect(
			stockStateForComponent({
				status: 'Retirado',
				lifecycleStatus: 'retirado',
				assignedPc: '',
				assignedUser: '',
				assignedFuero: '',
				buildOrderId: null
			})
		).toBe('retirado');
	});

	it('returns a filtered demo board with typed summary metrics', () => {
		const board = demoStockBoard({ query: 'monitor', state: 'disponible' });

		expect(board.mode).toBe('demo');
		expect(board.components.length).toBe(1);
		expect(board.components[0]).toEqual(
			expect.objectContaining({
				serialNumber: expect.any(String),
				componentType: 'Monitor',
				state: 'disponible'
			})
		);
		expect(board.summary).toEqual(
			expect.objectContaining({
				total: expect.any(Number),
				available: 1,
				assigned: expect.any(Number),
				reserved: expect.any(Number),
				retired: expect.any(Number)
			})
		);
	});
});
