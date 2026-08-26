import { describe, expect, it } from 'vitest';
import { createAppConfig } from './config';

describe('createAppConfig', () => {
	it('accepts legacy Flask DB_* variables as MySQL configuration', () => {
		const config = createAppConfig({
			DB_HOST: '127.0.0.1',
			DB_PORT: '3307',
			DB_NAME: 'inventario_dev',
			DB_USER: 'root',
			DB_PASS: 'local-password'
		});

		expect(config.MYSQL_HOST).toBe('127.0.0.1');
		expect(config.MYSQL_PORT).toBe(3307);
		expect(config.MYSQL_DATABASE).toBe('inventario_dev');
		expect(config.MYSQL_USER).toBe('root');
		expect(config.MYSQL_PASSWORD).toBe('local-password');
	});

	it('lets explicit MYSQL_* variables override legacy DB_* variables', () => {
		const config = createAppConfig({
			DB_HOST: '127.0.0.1',
			DB_NAME: 'inventario_dev',
			DB_USER: 'root',
			DB_PASS: 'legacy-password',
			MYSQL_HOST: '10.0.0.10',
			MYSQL_DATABASE: 'inventario_next',
			MYSQL_USER: 'next_user',
			MYSQL_PASSWORD: 'next-password'
		});

		expect(config.MYSQL_HOST).toBe('10.0.0.10');
		expect(config.MYSQL_DATABASE).toBe('inventario_next');
		expect(config.MYSQL_USER).toBe('next_user');
		expect(config.MYSQL_PASSWORD).toBe('next-password');
	});

	it('builds AD_URL from legacy AD_SERVER using plain LDAP by default', () => {
		const config = createAppConfig({
			AD_SERVER: '10.15.0.41'
		});

		expect(config.AD_URL).toBe('ldap://10.15.0.41:389');
	});

	it('builds AD_URL from legacy AD_SERVER using LDAPS when AD_USE_SSL is true', () => {
		const config = createAppConfig({
			AD_SERVER: 'ad.example.local',
			AD_USE_SSL: 'true'
		});

		expect(config.AD_URL).toBe('ldaps://ad.example.local:636');
	});

	it('keeps explicit AD_URL ahead of legacy AD_SERVER', () => {
		const config = createAppConfig({
			AD_URL: 'ldap://configured.example.local:389',
			AD_SERVER: 'ignored.example.local'
		});

		expect(config.AD_URL).toBe('ldap://configured.example.local:389');
	});
});
