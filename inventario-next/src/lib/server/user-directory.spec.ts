import { describe, expect, it } from 'vitest';
import { demoUserDirectory, requesterOptionsFromUsers } from './user-directory';

describe('user-directory', () => {
	it('returns a sanitized user contract without password hashes', () => {
		const directory = demoUserDirectory();

		expect(directory.mode).toBe('demo');
		expect(directory.users.length).toBeGreaterThan(0);
		expect(JSON.stringify(directory.users)).not.toContain('password_hash');
		expect(directory.users[0]).toEqual(
			expect.objectContaining({
				username: expect.any(String),
				displayName: expect.any(String),
				source: expect.stringMatching(/local|ad|linked/),
				permissions: expect.any(Array)
			})
		);
	});

	it('builds requester labels with fuero for task forms', () => {
		const directory = demoUserDirectory();
		const options = requesterOptionsFromUsers(directory.users);

		expect(options).toContainEqual({
			value: 'Gustavo Mock AD',
			label: 'Gustavo Mock AD (Sistemas)',
			fuero: 'Sistemas',
			username: 'gustavo.m'
		});
	});
});
