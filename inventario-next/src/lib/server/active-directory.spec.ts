import { describe, expect, it } from 'vitest';
import {
	buildAdBindCandidates,
	domainFromBaseDn,
	escapeLdapFilterValue,
	normalizeAdUsername
} from './active-directory';

describe('normalizeAdUsername', () => {
	it('removes domain prefixes and suffixes', () => {
		expect(normalizeAdUsername('PODJUDSP\\gmurad')).toBe('gmurad');
		expect(normalizeAdUsername('gmurad@podjudsp.local')).toBe('gmurad');
		expect(normalizeAdUsername(' gmurad ')).toBe('gmurad');
	});
});

describe('buildAdBindCandidates', () => {
	it('tries the domain UPN before the plain account name', () => {
		expect(buildAdBindCandidates('gmurad', 'podjudsp.local')).toEqual([
			'gmurad@podjudsp.local',
			'gmurad'
		]);
	});

	it('keeps an explicitly typed UPN as the first bind candidate', () => {
		expect(buildAdBindCandidates('gmurad@podjudsp.local', 'podjudsp.local')).toEqual([
			'gmurad@podjudsp.local',
			'gmurad'
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
