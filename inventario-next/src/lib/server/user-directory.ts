import { appConfig } from './config';
import { getMysqlPool } from './db';
import type { RowDataPacket } from 'mysql2';

export type UserSource = 'local' | 'ad' | 'linked';

export interface DirectoryUser {
	username: string;
	displayName: string;
	realName: string;
	fuero: string;
	phone: string;
	role: string;
	technicianName: string;
	source: UserSource;
	isActive: boolean;
	isSuperuser: boolean;
	mustChangePassword: boolean;
	permissions: string[];
}

export interface RequesterOption {
	value: string;
	label: string;
	fuero: string;
	username: string;
}

export interface UserDirectory {
	mode: 'demo' | 'mysql';
	query: string;
	users: DirectoryUser[];
	requesterOptions: RequesterOption[];
	summary: {
		total: number;
		active: number;
		adOnly: number;
		localOnly: number;
		linked: number;
	};
	note: string;
}

interface AppUserRow extends RowDataPacket {
	username: string;
	display_name?: string | null;
	is_superuser?: number | null;
	is_active?: number | null;
	must_change_password?: number | null;
	role?: string | null;
	technician_name?: string | null;
	phone?: string | null;
	can_access_dashboard?: number | null;
	can_access_mobile?: number | null;
	can_access_infrastructure?: number | null;
	can_access_reports?: number | null;
	can_audit_racks?: number | null;
	can_manage_stock?: number | null;
	can_access_operadores?: number | null;
	ad_real_name?: string | null;
	ad_fuero?: string | null;
	ad_phone?: string | null;
}

interface AdUserRow extends RowDataPacket {
	username: string;
	real_name?: string | null;
	fuero?: string | null;
	phone?: string | null;
}

const PERMISSION_COLUMNS: Array<[keyof AppUserRow, string]> = [
	['can_access_dashboard', 'Dashboard'],
	['can_access_mobile', 'Movil tecnicos'],
	['can_access_infrastructure', 'Infraestructura'],
	['can_access_reports', 'Reportes'],
	['can_audit_racks', 'Auditar racks'],
	['can_manage_stock', 'Stock'],
	['can_access_operadores', 'Operadores']
];

function bool(value: number | null | undefined) {
	return Number(value ?? 0) === 1;
}

function normalizeSearch(value: string) {
	return value
		.trim()
		.toLowerCase()
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '');
}

function permissionsFromRow(row: AppUserRow) {
	const permissions = PERMISSION_COLUMNS.filter(([column]) => bool(row[column])).map(
		([, label]) => label
	);
	if (bool(row.is_superuser)) permissions.unshift('Administrador');
	return permissions;
}

function appRowToUser(row: AppUserRow): DirectoryUser {
	const realName = row.ad_real_name ?? row.display_name ?? row.username;
	return {
		username: row.username,
		displayName: row.display_name ?? realName,
		realName,
		fuero: row.ad_fuero ?? '',
		phone: row.phone || row.ad_phone || '',
		role: row.role ?? 'usuario',
		technicianName: row.technician_name ?? '',
		source: row.ad_real_name ? 'linked' : 'local',
		isActive: bool(row.is_active),
		isSuperuser: bool(row.is_superuser),
		mustChangePassword: bool(row.must_change_password),
		permissions: permissionsFromRow(row)
	};
}

function adRowToUser(row: AdUserRow): DirectoryUser {
	return {
		username: row.username,
		displayName: row.real_name ?? row.username,
		realName: row.real_name ?? row.username,
		fuero: row.fuero ?? '',
		phone: row.phone ?? '',
		role: 'AD',
		technicianName: '',
		source: 'ad',
		isActive: true,
		isSuperuser: false,
		mustChangePassword: false,
		permissions: []
	};
}

function filterUsers(users: DirectoryUser[], query: string) {
	const normalizedQuery = normalizeSearch(query);
	if (!normalizedQuery) return users;

	return users.filter((user) =>
		normalizeSearch(
			`${user.username} ${user.displayName} ${user.realName} ${user.fuero} ${user.role}`
		).includes(normalizedQuery)
	);
}

export function requesterOptionsFromUsers(users: DirectoryUser[]): RequesterOption[] {
	return users
		.filter((user) => user.realName || user.displayName)
		.map((user) => {
			const value = user.realName || user.displayName;
			return {
				value,
				label: user.fuero ? `${value} (${user.fuero})` : value,
				fuero: user.fuero,
				username: user.username
			};
		})
		.sort((left, right) => left.label.localeCompare(right.label, 'es'));
}

function summarize(users: DirectoryUser[]) {
	return {
		total: users.length,
		active: users.filter((user) => user.isActive).length,
		adOnly: users.filter((user) => user.source === 'ad').length,
		localOnly: users.filter((user) => user.source === 'local').length,
		linked: users.filter((user) => user.source === 'linked').length
	};
}

export function demoUserDirectory(query = ''): UserDirectory {
	const users = filterUsers(
		[
			{
				username: 'gustavo.m',
				displayName: 'Gustavo Mock AD',
				realName: 'Gustavo Mock AD',
				fuero: 'Sistemas',
				phone: '1234',
				role: 'tecnico',
				technicianName: 'Gustavo Mock AD',
				source: 'linked',
				isActive: true,
				isSuperuser: false,
				mustChangePassword: false,
				permissions: ['Movil tecnicos']
			},
			{
				username: 'administrador',
				displayName: 'Administrador Inicial',
				realName: 'Administrador Inicial',
				fuero: '',
				phone: '',
				role: 'administrador',
				technicianName: '',
				source: 'local',
				isActive: true,
				isSuperuser: true,
				mustChangePassword: false,
				permissions: ['Administrador', 'Dashboard', 'Reportes']
			},
			{
				username: 'andrea',
				displayName: 'Andrea Gomez',
				realName: 'Andrea Gomez',
				fuero: 'Recursos Humanos',
				phone: '2222',
				role: 'AD',
				technicianName: '',
				source: 'ad',
				isActive: true,
				isSuperuser: false,
				mustChangePassword: false,
				permissions: []
			}
		],
		query
	);

	return {
		mode: 'demo',
		query,
		users,
		requesterOptions: requesterOptionsFromUsers(users),
		summary: summarize(users),
		note: 'Sin .env local: usuarios demo, no se consulto MySQL.'
	};
}

export async function loadUserDirectory({
	query = '',
	limit = 80
}: {
	query?: string;
	limit?: number;
} = {}): Promise<UserDirectory> {
	const trimmedQuery = query.trim();
	if (!appConfig.MYSQL_PASSWORD) return demoUserDirectory(trimmedQuery);

	const likeQuery = `%${trimmedQuery}%`;
	const pool = getMysqlPool();
	const [appRows] = await pool.query<AppUserRow[]>(
		`
		SELECT
			u.username, u.display_name, u.is_superuser, u.is_active, u.must_change_password,
			u.role, u.technician_name, u.phone, u.can_access_dashboard, u.can_access_mobile,
			u.can_access_infrastructure, u.can_access_reports, u.can_audit_racks,
			u.can_manage_stock, u.can_access_operadores,
			ad.real_name AS ad_real_name, ad.fuero AS ad_fuero, ad.phone AS ad_phone
		FROM app_users u
		LEFT JOIN ad_users ad ON LOWER(TRIM(ad.username)) = LOWER(TRIM(u.username))
		WHERE ? = ''
		   OR u.username LIKE ?
		   OR u.display_name LIKE ?
		   OR u.role LIKE ?
		   OR ad.real_name LIKE ?
		   OR ad.fuero LIKE ?
		ORDER BY u.is_active DESC, u.display_name, u.username
		LIMIT ?
		`,
		[trimmedQuery, likeQuery, likeQuery, likeQuery, likeQuery, likeQuery, limit]
	);
	const [adRows] = await pool.query<AdUserRow[]>(
		`
		SELECT ad.username, ad.real_name, ad.fuero, ad.phone
		FROM ad_users ad
		LEFT JOIN app_users u ON LOWER(TRIM(u.username)) = LOWER(TRIM(ad.username))
		WHERE u.username IS NULL
		  AND (
			? = ''
			OR ad.username LIKE ?
			OR ad.real_name LIKE ?
			OR ad.fuero LIKE ?
		  )
		ORDER BY ad.real_name, ad.username
		LIMIT ?
		`,
		[trimmedQuery, likeQuery, likeQuery, likeQuery, limit]
	);

	const users = [...appRows.map(appRowToUser), ...adRows.map(adRowToUser)].slice(0, limit);

	return {
		mode: 'mysql',
		query: trimmedQuery,
		users,
		requesterOptions: requesterOptionsFromUsers(users),
		summary: summarize(users),
		note: appConfig.MYSQL_READ_ONLY
			? 'MySQL conectado en modo lectura.'
			: 'MySQL conectado con escritura habilitada por configuracion.'
	};
}
