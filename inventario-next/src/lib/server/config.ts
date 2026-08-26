import { env } from '$env/dynamic/private';
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

export const appConfig = envSchema.parse(env);
