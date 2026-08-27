import { json } from '@sveltejs/kit';
import { resolveActiveDirectoryConfig } from '$lib/server/active-directory';
import { appConfig } from '$lib/server/config';

export async function GET() {
	return json({
		status: 'ok',
		app: 'inventario-next',
		env: appConfig.APP_ENV,
		mysqlReadOnly: appConfig.MYSQL_READ_ONLY,
		activeDirectoryConfigured: Boolean(await resolveActiveDirectoryConfig())
	});
}
