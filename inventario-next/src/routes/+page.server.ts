import { loadDashboardSummary } from '$lib/server/dashboard-summary';

export async function load() {
	return loadDashboardSummary();
}
