import { appConfig } from './config';
import { getMysqlPool } from './db';
import type { RowDataPacket } from 'mysql2';

export interface DashboardMetricSet {
	activePcs: number;
	assignedComponents: number;
	openTasks: number;
	pendingValidation: number;
}

export interface DashboardEfemeride {
	title: string;
	description: string;
	icon: string;
}

export interface DashboardSummary {
	mode: 'demo' | 'mysql';
	metrics: DashboardMetricSet;
	todayEfemerides: DashboardEfemeride[];
	note: string;
}

interface CountRow extends RowDataPacket {
	total: number;
}

interface EfemerideRow extends RowDataPacket {
	titulo?: string | null;
	descripcion?: string | null;
	icono?: string | null;
}

export function demoDashboardSummary(): DashboardSummary {
	return {
		mode: 'demo',
		metrics: {
			activePcs: 2,
			assignedComponents: 4,
			openTasks: 3,
			pendingValidation: 1
		},
		todayEfemerides: [],
		note: 'Sin .env local: resumen demo, no se consulto MySQL.'
	};
}

async function count(sql: string, params: unknown[] = []) {
	const [rows] = await getMysqlPool().query<CountRow[]>(sql, params);
	return Number(rows[0]?.total ?? 0);
}

function todayDiaMes() {
	return new Intl.DateTimeFormat('es-AR', {
		timeZone: 'America/Argentina/Buenos_Aires',
		month: '2-digit',
		day: '2-digit'
	})
		.format(new Date())
		.replace('/', '-');
}

export async function loadDashboardSummary(): Promise<DashboardSummary> {
	if (!appConfig.MYSQL_PASSWORD) return demoDashboardSummary();

	const [activePcs, assignedComponents, openTasks, pendingValidation] = await Promise.all([
		count('SELECT COUNT(*) total FROM pcs WHERE is_active = 1'),
		count(
			`
			SELECT COUNT(*) total
			FROM components
			WHERE assigned_pc IS NOT NULL
			  AND (
				status IN ('Installed', 'Instalado')
				OR lifecycle_status IN ('desplegado', 'deployed')
			  )
			`
		),
		count("SELECT COUNT(*) total FROM tasks WHERE estado IN ('Pendiente', 'Asignada')"),
		count("SELECT COUNT(*) total FROM pcs WHERE validation_status IN ('pendiente', 'sin_gemelo')")
	]);

	const [efemerideRows] = await getMysqlPool().query<EfemerideRow[]>(
		`
		SELECT titulo, descripcion, icono
		FROM efemerides
		WHERE dia_mes = ?
		  AND COALESCE(is_active, 1) = 1
		ORDER BY titulo
		`,
		[todayDiaMes()]
	);

	return {
		mode: 'mysql',
		metrics: {
			activePcs,
			assignedComponents,
			openTasks,
			pendingValidation
		},
		todayEfemerides: efemerideRows.map((row) => ({
			title: row.titulo ?? 'Efemeride',
			description: row.descripcion ?? '',
			icon: row.icono ?? ''
		})),
		note: appConfig.MYSQL_READ_ONLY
			? 'MySQL conectado en modo lectura.'
			: 'MySQL conectado con escritura habilitada por configuracion.'
	};
}
