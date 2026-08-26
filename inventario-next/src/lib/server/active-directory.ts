import { Client } from 'ldapts';
import { appConfig } from './config';

export function isActiveDirectoryConfigured() {
	return Boolean(appConfig.AD_URL && appConfig.AD_BASE_DN);
}

export function createActiveDirectoryClient() {
	return new Client({
		url: appConfig.AD_URL,
		tlsOptions: {
			rejectUnauthorized: appConfig.AD_TLS_REJECT_UNAUTHORIZED
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
	const candidates = [];

	if (trimmed.includes('@') || trimmed.includes('\\')) candidates.push(trimmed);
	if (domain && normalized) candidates.push(`${normalized}@${domain}`);
	if (normalized) candidates.push(normalized);
	if (trimmed) candidates.push(trimmed);

	return [...new Set(candidates)];
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
	username: string
): Promise<ActiveDirectoryUser | null> {
	if (!appConfig.AD_BASE_DN) return null;

	const normalized = normalizeAdUsername(username);
	const result = await client.search(appConfig.AD_BASE_DN, {
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
	clientFactory: () => ActiveDirectoryClient = () =>
		createActiveDirectoryClient() as unknown as ActiveDirectoryClient
): Promise<ActiveDirectoryUser | null> {
	if (!isActiveDirectoryConfigured() || !username.trim() || !password) return null;

	const domain = appConfig.AD_DOMAIN || domainFromBaseDn(appConfig.AD_BASE_DN);
	for (const bindUser of buildAdBindCandidates(username, domain)) {
		const client = clientFactory();
		try {
			await client.bind(bindUser, password);
			const user = await loadActiveDirectoryUser(client, username);
			return (
				user ?? {
					username: normalizeAdUsername(username),
					displayName: normalizeAdUsername(username),
					mail: null
				}
			);
		} catch {
			// Try the next bind format without leaking which one failed.
		} finally {
			try {
				await client.unbind();
			} catch {
				// Closing a failed LDAP connection is best-effort.
			}
		}
	}

	return null;
}
