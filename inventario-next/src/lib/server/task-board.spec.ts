import { describe, expect, it } from 'vitest';
import { demoTaskBoard, requesterLabelForTask } from './task-board';

describe('task-board', () => {
	it('enriches requester labels with fuero from AD users', () => {
		const label = requesterLabelForTask({ requester: 'DOMINIO\\gustavo.m', fuero: '' }, [
			{ username: 'gustavo.m', realName: 'Gustavo Mock AD', fuero: 'Sistemas' }
		]);

		expect(label).toBe('Gustavo Mock AD (Sistemas)');
	});

	it('returns a demo board contract with open and recent tasks', () => {
		const board = demoTaskBoard();

		expect(board.mode).toBe('demo');
		expect(board.tasks.length).toBeGreaterThan(0);
		expect(board.summary).toEqual(
			expect.objectContaining({
				total: expect.any(Number),
				open: expect.any(Number),
				done: expect.any(Number)
			})
		);
		expect(board.tasks[0]).toEqual(
			expect.objectContaining({
				id: expect.any(Number),
				requesterLabel: expect.stringContaining('(')
			})
		);
	});
});
