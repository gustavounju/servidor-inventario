import { json } from '@sveltejs/kit';
import { isActiveDirectoryConfigured } from '$lib/server/active-directory';
import { appConfig } from '$lib/server/config';

export function GET() {
	return json({
		status: 'ok',
		app: 'inventario-next',
		env: appConfig.APP_ENV,
		mysqlReadOnly: appConfig.MYSQL_READ_ONLY,
		activeDirectoryConfigured: isActiveDirectoryConfigured()
	});
}
