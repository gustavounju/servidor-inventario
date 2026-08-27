import { afterEach, describe, expect, it, vi } from 'vitest';
import { appConfig } from './config';
import {
	authenticateActiveDirectoryPassword,
	buildAdBindCandidates,
	domainFromBaseDn,
	escapeLdapFilterValue,
	normalizeAdUsername
} from './active-directory';

const originalConfig = { ...appConfig };

function configureActiveDirectory() {
	Object.assign(appConfig, {
		AD_URL: 'ldap://ad.example.local:389',
		AD_BASE_DN: 'DC=podjudsp,DC=local',
		AD_DOMAIN: 'podjudsp.local'
	});
}

afterEach(() => {
	Object.assign(appConfig, originalConfig);
	vi.restoreAllMocks();
});

describe('normalizeAdUsername', () => {
	it('removes domain prefixes and suffixes', () => {
		expect(normalizeAdUsername('PODJUDSP\\gmurad')).toBe('gmurad');
		expect(normalizeAdUsername('gmurad@podjudsp.local')).toBe('gmurad');
		expect(normalizeAdUsername(' gmurad ')).toBe('gmurad');
	});
});

describe('buildAdBindCandidates', () => {
	it('uses a single domain UPN for plain account names', () => {
		expect(buildAdBindCandidates('gmurad', 'podjudsp.local')).toEqual(['gmurad@podjudsp.local']);
	});

	it('keeps an explicitly typed UPN as the only bind candidate', () => {
		expect(buildAdBindCandidates('gmurad@podjudsp.local', 'podjudsp.local')).toEqual([
			'gmurad@podjudsp.local'
		]);
	});

	it('keeps an explicitly typed domain account as the only bind candidate', () => {
		expect(buildAdBindCandidates('PODJUDSP\\gmurad', 'podjudsp.local')).toEqual([
			'PODJUDSP\\gmurad'
		]);
	});
});

describe('escapeLdapFilterValue', () => {
	it('escapes LDAP filter metacharacters', () => {
		expect(escapeLdapFilterValue('a*(b)\\c\0')).toBe('a\\2a\\28b\\29\\5cc\\00');
	});
});

describe('domainFromBaseDn', () => {
	it('builds a DNS domain from dc components', () => {
		expect(domainFromBaseDn('OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local')).toBe('podjudsp.local');
	});
});

describe('authenticateActiveDirectoryPassword', () => {
	it('does a single bind attempt when credentials are invalid', async () => {
		configureActiveDirectory();
		const bind = vi.fn().mockRejectedValue(new Error('invalid credentials'));
		const search = vi.fn();
		const unbind = vi.fn().mockResolvedValue(undefined);
		const clientFactory = vi.fn(() => ({ bind, search, unbind }));

		await expect(
			authenticateActiveDirectoryPassword('gmurad', 'bad-password', clientFactory)
		).resolves.toBeNull();

		expect(clientFactory).toHaveBeenCalledTimes(1);
		expect(bind).toHaveBeenCalledOnce();
		expect(bind).toHaveBeenCalledWith('gmurad@podjudsp.local', 'bad-password');
		expect(search).not.toHaveBeenCalled();
	});

	it('does not retry bind when search fails after a successful bind', async () => {
		configureActiveDirectory();
		const bind = vi.fn().mockResolvedValue(undefined);
		const search = vi.fn().mockRejectedValue(new Error('search unavailable'));
		const unbind = vi.fn().mockResolvedValue(undefined);
		const clientFactory = vi.fn(() => ({ bind, search, unbind }));

		await expect(
			authenticateActiveDirectoryPassword('gmurad', 'correct-password', clientFactory)
		).resolves.toEqual({
			username: 'gmurad',
			displayName: 'gmurad',
			mail: null
		});

		expect(clientFactory).toHaveBeenCalledTimes(1);
		expect(bind).toHaveBeenCalledOnce();
		expect(search).toHaveBeenCalledOnce();
	});
});
