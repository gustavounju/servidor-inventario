import { Client } from 'ldapts';
import { appConfig } from './config';
import { getMysqlPool } from './db';
import type { RowDataPacket } from 'mysql2';

export function isActiveDirectoryConfigured() {
	return Boolean(appConfig.AD_URL && appConfig.AD_BASE_DN);
}

interface ActiveDirectoryConfig {
	url: string;
	baseDn: string;
	domain: string;
	tlsRejectUnauthorized: boolean;
}

interface AppSettingRow extends RowDataPacket {
	setting_key: string;
	setting_value: string | null;
}

const AD_SETTING_KEYS = [
	'AD_URL',
	'AD_SERVER',
	'AD_BASE_DN',
	'AD_DOMAIN',
	'AD_USE_SSL',
	'AD_TLS_REJECT_UNAUTHORIZED'
] as const;

function parseBoolean(value: string | undefined, defaultValue: boolean) {
	if (value === undefined) return defaultValue;
	return value.trim().toLowerCase() === 'true';
}

function buildAdUrl(server: string, useSsl: boolean) {
	const trimmed = server.trim();
	if (!trimmed) return '';
	if (/^ldaps?:\/\//i.test(trimmed)) return trimmed;

	const protocol = useSsl ? 'ldaps' : 'ldap';
	const hasPort = /:\d+$/.test(trimmed);
	const port = useSsl ? 636 : 389;
	return `${protocol}://${trimmed}${hasPort ? '' : `:${port}`}`;
}

async function loadLegacyActiveDirectorySettings() {
	if (!appConfig.MYSQL_PASSWORD) return {};

	try {
		const placeholders = AD_SETTING_KEYS.map(() => '?').join(', ');
		const [rows] = await getMysqlPool().query<AppSettingRow[]>(
			`SELECT setting_key, setting_value
			 FROM app_settings
			 WHERE is_active = 1 AND setting_key IN (${placeholders})`,
			[...AD_SETTING_KEYS]
		);

		return Object.fromEntries(
			rows
				.filter((row) => row.setting_value !== null)
				.map((row) => [row.setting_key, String(row.setting_value).trim()])
		) as Partial<Record<(typeof AD_SETTING_KEYS)[number], string>>;
	} catch {
		return {};
	}
}

export async function resolveActiveDirectoryConfig(): Promise<ActiveDirectoryConfig | null> {
	const legacySettings =
		appConfig.AD_URL && appConfig.AD_BASE_DN ? {} : await loadLegacyActiveDirectorySettings();
	const useSsl = parseBoolean(legacySettings.AD_USE_SSL, appConfig.AD_USE_SSL);
	const url =
		appConfig.AD_URL || legacySettings.AD_URL || buildAdUrl(legacySettings.AD_SERVER ?? '', useSsl);
	const baseDn = appConfig.AD_BASE_DN || legacySettings.AD_BASE_DN || '';
	const domain = appConfig.AD_DOMAIN || legacySettings.AD_DOMAIN || domainFromBaseDn(baseDn);
	const tlsRejectUnauthorized = parseBoolean(
		legacySettings.AD_TLS_REJECT_UNAUTHORIZED,
		appConfig.AD_TLS_REJECT_UNAUTHORIZED
	);

	if (!url || !baseDn) return null;

	return {
		url,
		baseDn,
		domain,
		tlsRejectUnauthorized
	};
}

export function createActiveDirectoryClient(config: ActiveDirectoryConfig) {
	return new Client({
		url: config.url,
		tlsOptions: {
			rejectUnauthorized: config.tlsRejectUnauthorized
		}
	});
}

export interface ActiveDirectoryUser {
	username: string;
	displayName: string;
	mail: string | null;
}

interface LdapSearchEntry {
	sAMAccountName?: string | string[];
	displayName?: string | string[];
	mail?: string | string[];
}

interface ActiveDirectoryClient {
	bind(user: string, password: string): Promise<void>;
	search(
		baseDn: string,
		options: { scope: 'sub'; filter: string; attributes: string[] }
	): Promise<{ searchEntries: LdapSearchEntry[] }>;
	unbind(): Promise<void>;
}

function firstString(value: string | string[] | undefined): string | undefined {
	if (Array.isArray(value)) return value.find(Boolean);
	return value || undefined;
}

export function normalizeAdUsername(username: string) {
	const trimmed = username.trim();
	if (!trimmed) return '';
	const withoutDomainPrefix = trimmed.includes('\\')
		? trimmed.split('\\').pop() || trimmed
		: trimmed;
	return withoutDomainPrefix.includes('@')
		? withoutDomainPrefix.split('@')[0]
		: withoutDomainPrefix;
}

export function buildAdBindCandidates(username: string, domain = '') {
	const trimmed = username.trim();
	const normalized = normalizeAdUsername(trimmed);
	if (trimmed.includes('@') || trimmed.includes('\\')) return [trimmed];
	if (domain && normalized) return [`${normalized}@${domain}`];
	if (normalized) return [normalized];
	return [];
}

export function domainFromBaseDn(baseDn: string) {
	const parts = baseDn
		.split(',')
		.map((part) => part.trim())
		.map((part) => /^dc=(.+)$/i.exec(part)?.[1])
		.filter((part): part is string => Boolean(part));
	return parts.join('.');
}

export function escapeLdapFilterValue(value: string) {
	return value.replace(/[\0()*\\]/g, (char) => {
		switch (char) {
			case '\0':
				return '\\00';
			case '(':
				return '\\28';
			case ')':
				return '\\29';
			case '*':
				return '\\2a';
			case '\\':
				return '\\5c';
			default:
				return char;
		}
	});
}

async function loadActiveDirectoryUser(
	client: ActiveDirectoryClient,
	config: ActiveDirectoryConfig,
	username: string
): Promise<ActiveDirectoryUser | null> {
	const normalized = normalizeAdUsername(username);
	const result = await client.search(config.baseDn, {
		scope: 'sub',
		filter: `(sAMAccountName=${escapeLdapFilterValue(normalized)})`,
		attributes: ['sAMAccountName', 'displayName', 'mail']
	});
	const entry = result.searchEntries[0];
	if (!entry) return null;

	const accountName = firstString(entry.sAMAccountName) ?? normalized;
	const displayName = firstString(entry.displayName) ?? accountName;
	return {
		username: accountName,
		displayName,
		mail: firstString(entry.mail) ?? null
	};
}

export async function authenticateActiveDirectoryPassword(
	username: string,
	password: string,
	clientFactory: (config: ActiveDirectoryConfig) => ActiveDirectoryClient = (config) =>
		createActiveDirectoryClient(config) as unknown as ActiveDirectoryClient
): Promise<ActiveDirectoryUser | null> {
	if (!username.trim() || !password) return null;

	const config = await resolveActiveDirectoryConfig();
	if (!config) return null;

	const bindUser = buildAdBindCandidates(username, config.domain)[0];
	if (!bindUser) return null;

	const client = clientFactory(config);
	try {
		await client.bind(bindUser, password);
		try {
			const user = await loadActiveDirectoryUser(client, config, username);
			if (user) return user;
		} catch {
			// Authentication already succeeded; a search/config issue must not retry
			// another bind and create extra failed-login noise in Active Directory.
		}
		return {
			username: normalizeAdUsername(username),
			displayName: normalizeAdUsername(username),
			mail: null
		};
	} catch {
		return null;
	} finally {
		try {
			await client.unbind();
		} catch {
			// Closing a failed LDAP connection is best-effort.
		}
	}
}
