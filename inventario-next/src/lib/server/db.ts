import { drizzle } from 'drizzle-orm/mysql2';
import mysql from 'mysql2/promise';
import { appConfig } from './config';

let pool: mysql.Pool | undefined;

export function getMysqlPool() {
	if (!pool) {
		pool = mysql.createPool({
			host: appConfig.MYSQL_HOST,
			port: appConfig.MYSQL_PORT,
			database: appConfig.MYSQL_DATABASE,
			user: appConfig.MYSQL_USER,
			password: appConfig.MYSQL_PASSWORD,
			waitForConnections: true,
			connectionLimit: 5,
			namedPlaceholders: true,
			multipleStatements: false
		});
	}

	return pool;
}

export function getDb() {
	return drizzle(getMysqlPool());
}

export async function pingDatabase() {
	const connection = await getMysqlPool().getConnection();
	try {
		await connection.query('SELECT 1');
		return true;
	} finally {
		connection.release();
	}
}
