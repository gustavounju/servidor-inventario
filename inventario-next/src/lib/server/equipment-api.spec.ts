import { describe, expect, it } from 'vitest';
import { GET } from '../../routes/api/equipos/[pcName]/detail/+server';

describe('GET /api/equipos/[pcName]/detail', () => {
	it('returns the reconciled equipment detail as JSON', async () => {
		const response = await GET({
			params: { pcName: 'demo' }
		} as Parameters<typeof GET>[0]);
		const payload = await response.json();

		expect(response.status).toBe(200);
		expect(payload.mode).toBe('demo');
		expect(payload.detail.pcName).toBe('demo');
		expect(payload.detail.monitors.length).toBeGreaterThan(0);
		expect(payload.detail.discrepancies[0]).toEqual(
			expect.objectContaining({
				code: expect.any(String),
				recommendedAction: expect.any(String)
			})
		);
	});
});
