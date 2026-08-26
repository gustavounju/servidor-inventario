import { appConfig } from './config';
import { getMysqlPool } from './db';
import type { RowDataPacket } from 'mysql2';

export interface EquipmentSearchItem {
	pcName: string;
	userName: string;
	fuero: string;
	monitorSummary: string;
	storageSummary: string;
}

export interface EquipmentSearchResult {
	mode: 'demo' | 'mysql';
	query: string;
	items: EquipmentSearchItem[];
	note: string;
}

interface EquipmentSearchRow extends RowDataPacket {
	pc_name?: string | null;
	last_user?: string | null;
	fuero?: string | null;
	monitors?: string | null;
	disk_models?: string | null;
}

const DEMO_ITEMS: EquipmentSearchItem[] = [
	{
		pcName: 'demo',
		userName: 'Demo Sistemas',
		fuero: 'Civil',
		monitorSummary: 'Philips 241V8 + LG 19EN33',
		storageSummary: 'KINGSTON 240GB + Seagate 500GB'
	},
	{
		pcName: 'JCC8SEC1600006',
		userName: 'Mesa de Entradas',
		fuero: 'Penal',
		monitorSummary: 'Samsung LS22',
		storageSummary: 'SSD 240GB'
	}
];

function normalizeSearch(value: string) {
	return value
		.trim()
		.toLowerCase()
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '');
}

function rowToSearchItem(row: EquipmentSearchRow): EquipmentSearchItem {
	return {
		pcName: row.pc_name ?? 'Sin nombre',
		userName: row.last_user ?? 'Sin usuario',
		fuero: row.fuero ?? 'Sin fuero',
		monitorSummary: row.monitors ?? 'Sin monitores informados',
		storageSummary: row.disk_models ?? 'Sin discos informados'
	};
}

function filterDemoItems(query: string) {
	const normalizedQuery = normalizeSearch(query);
	if (!normalizedQuery) return DEMO_ITEMS;

	return DEMO_ITEMS.filter((item) =>
		normalizeSearch(`${item.pcName} ${item.userName} ${item.fuero}`).includes(normalizedQuery)
	);
}

export async function searchEquipment({
	query = '',
	limit = 25
}: {
	query?: string;
	limit?: number;
}): Promise<EquipmentSearchResult> {
	const trimmedQuery = query.trim();

	if (!appConfig.MYSQL_PASSWORD) {
		return {
			mode: 'demo',
			query: trimmedQuery,
			items: filterDemoItems(trimmedQuery).slice(0, limit),
			note: 'Sin .env local: listado demo, no se consulto MySQL.'
		};
	}

	const pool = getMysqlPool();
	const likeQuery = `%${trimmedQuery}%`;
	const [rows] = await pool.query<EquipmentSearchRow[]>(
		`
		SELECT pc_name, last_user, fuero, monitors, disk_models
		FROM pcs
		WHERE ? = ''
		   OR pc_name LIKE ?
		   OR last_user LIKE ?
		   OR fuero LIKE ?
		ORDER BY pc_name
		LIMIT ?
		`,
		[trimmedQuery, likeQuery, likeQuery, likeQuery, limit]
	);

	return {
		mode: 'mysql',
		query: trimmedQuery,
		items: rows.map(rowToSearchItem),
		note: appConfig.MYSQL_READ_ONLY
			? 'MySQL conectado en modo lectura.'
			: 'MySQL conectado con escritura habilitada por configuracion.'
	};
}
