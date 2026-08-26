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
	AD_BASE_DN: z.string().default(''),
	AD_DOMAIN: z.string().default(''),
	AD_SYNC_USER: z.string().default(''),
	AD_SYNC_PASSWORD: z.string().default(''),
	AD_TLS_REJECT_UNAUTHORIZED: z
		.string()
		.optional()
		.transform((value) => String(value ?? 'true').toLowerCase() !== 'false'),
	TLS_CERT_PATH: z.string().default('../cert.pem'),
	TLS_KEY_PATH: z.string().default('../key.pem')
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

export function createAppConfig(input: EnvInput = {}) {
	return envSchema.parse(withLegacyMysqlAliases(input));
}

const parentEnv = process.env.VITEST ? {} : parseEnvFile(resolve(process.cwd(), '..', '.env'));

export const appConfig = createAppConfig({
	...parentEnv,
	...env
});
