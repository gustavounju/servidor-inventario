import { env } from '$env/dynamic/private';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { z } from 'zod';

const envSchema = z.object({
	APP_ENV: z.string().default('local'),
	MYSQL_HOST: z.string().default('127.0.0.1'),
	MYSQL_PORT: z.coerce.number().int().positive().default(3306),
	MYSQL_DATABASE: z.string().default('inventario_dev'),
	MYSQL_USER: z.string().default('inventario_user'),
	MYSQL_PASSWORD: z.string().default(''),
	MYSQL_READ_ONLY: z
		.string()
		.optional()
		.transform((value) => String(value ?? 'true').toLowerCase() !== 'false'),
	AD_URL: z.string().default(''),
	AD_SERVER: z.string().default(''),
	AD_BASE_DN: z.string().default(''),
	AD_DOMAIN: z.string().default(''),
	AD_SYNC_USER: z.string().default(''),
	AD_SYNC_PASSWORD: z.string().default(''),
	AD_USE_SSL: z
		.string()
		.optional()
		.transform((value) => String(value ?? 'false').toLowerCase() === 'true'),
	AD_TLS_REJECT_UNAUTHORIZED: z
		.string()
		.optional()
		.transform((value) => String(value ?? 'true').toLowerCase() !== 'false'),
	TRUST_PROXY: z
		.string()
		.optional()
		.transform((value) => String(value ?? 'false').toLowerCase() === 'true'),
	TLS_CERT_PATH: z.string().default('../cert.pem'),
	TLS_KEY_PATH: z.string().default('../key.pem'),
	AUTH_SECRET: z.string().default('dev-only-secret-change-in-production')
});

type EnvInput = Record<string, string | undefined>;

function parseEnvFile(path: string): EnvInput {
	if (!existsSync(path)) return {};

	return Object.fromEntries(
		readFileSync(path, 'utf8')
			.split(/\r?\n/)
			.filter((line) => /^\s*[^#][^=]+=/.test(line))
			.map((line) => {
				const index = line.indexOf('=');
				return [
					line.slice(0, index).trim(),
					line
						.slice(index + 1)
						.trim()
						.replace(/^['"]|['"]$/g, '')
				];
			})
	);
}

function withLegacyMysqlAliases(input: EnvInput): EnvInput {
	return {
		...input,
		MYSQL_HOST: input.MYSQL_HOST ?? input.DB_HOST,
		MYSQL_PORT: input.MYSQL_PORT ?? input.DB_PORT,
		MYSQL_DATABASE: input.MYSQL_DATABASE ?? input.DB_NAME,
		MYSQL_USER: input.MYSQL_USER ?? input.DB_USER,
		MYSQL_PASSWORD: input.MYSQL_PASSWORD ?? input.DB_PASS
	};
}

function legacyAdUrl(input: EnvInput): string | undefined {
	if (input.AD_URL) return input.AD_URL;
	const server = input.AD_SERVER?.trim();
	if (!server) return undefined;
	if (/^ldaps?:\/\//i.test(server)) return server;

	const useSsl = String(input.AD_USE_SSL ?? 'false').toLowerCase() === 'true';
	const protocol = useSsl ? 'ldaps' : 'ldap';
	const hasPort = /:\d+$/.test(server);
	const port = useSsl ? 636 : 389;
	return `${protocol}://${server}${hasPort ? '' : `:${port}`}`;
}

function withLegacyAdAliases(input: EnvInput): EnvInput {
	return {
		...input,
		AD_URL: legacyAdUrl(input) ?? input.AD_URL
	};
}

export function createAppConfig(input: EnvInput = {}) {
	const config = envSchema.parse(withLegacyAdAliases(withLegacyMysqlAliases(input)));
	const isProduction = config.APP_ENV.trim().toLowerCase() === 'production';

	if (
		isProduction &&
		(!config.AUTH_SECRET ||
			config.AUTH_SECRET === 'dev-only-secret-change-in-production' ||
			config.AUTH_SECRET.length < 32)
	) {
		throw new Error(
			'AUTH_SECRET must be set to a non-default value of at least 32 characters in production'
		);
	}

	return config;
}

const parentEnv = process.env.VITEST ? {} : parseEnvFile(resolve(process.cwd(), '..', '.env'));

export const appConfig = createAppConfig({
	...parentEnv,
	...env
});
