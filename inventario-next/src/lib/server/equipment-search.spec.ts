import { describe, expect, it } from 'vitest';
import { searchEquipment } from './equipment-search';

describe('searchEquipment', () => {
	it('returns demo equipment when MySQL is not configured', async () => {
		const result = await searchEquipment({ query: '' });

		expect(result.mode).toBe('demo');
		expect(result.items.length).toBeGreaterThan(0);
		expect(result.items[0]).toEqual(
			expect.objectContaining({
				pcName: expect.any(String),
				userName: expect.any(String),
				fuero: expect.any(String)
			})
		);
	});

	it('filters demo equipment by pc name or user', async () => {
		const byPc = await searchEquipment({ query: 'demo' });
		const byUser = await searchEquipment({ query: 'sistemas' });

		expect(byPc.items.map((item) => item.pcName)).toContain('demo');
		expect(byUser.items.some((item) => item.userName.includes('Sistemas'))).toBe(true);
	});
});
