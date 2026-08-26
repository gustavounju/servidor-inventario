import { describe, expect, it } from 'vitest';
import { demoDashboardSummary } from './dashboard-summary';

describe('demoDashboardSummary', () => {
	it('returns the dashboard contract without needing MySQL', () => {
		const summary = demoDashboardSummary();

		expect(summary.mode).toBe('demo');
		expect(summary.metrics).toEqual(
			expect.objectContaining({
				activePcs: expect.any(Number),
				assignedComponents: expect.any(Number),
				openTasks: expect.any(Number),
				pendingValidation: expect.any(Number),
				activeUsers: expect.any(Number)
			})
		);
		expect(Array.isArray(summary.todayEfemerides)).toBe(true);
	});
});
