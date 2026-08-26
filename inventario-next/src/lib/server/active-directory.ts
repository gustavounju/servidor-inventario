import { Client } from 'ldapts';
import { appConfig } from './config';

export function isActiveDirectoryConfigured() {
	return Boolean(appConfig.AD_URL && appConfig.AD_BASE_DN && appConfig.AD_SYNC_USER);
}

export function createActiveDirectoryClient() {
	return new Client({
		url: appConfig.AD_URL,
		tlsOptions: {
			rejectUnauthorized: appConfig.AD_TLS_REJECT_UNAUTHORIZED
		}
	});
}
