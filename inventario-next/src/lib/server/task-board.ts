import { appConfig } from './config';
import { getMysqlPool } from './db';
import type { RowDataPacket } from 'mysql2';

export interface TaskRequesterSeed {
	requester: string;
	fuero: string;
}

export interface TaskAdUser {
	username: string;
	realName: string;
	fuero: string;
}

export interface TaskListItem {
	id: number;
	pcName: string;
	createdAt: string;
	description: string;
	status: string;
	requester: string;
	requesterLabel: string;
	fuero: string;
	category: string;
	assignedTo: string;
	priority: number;
	completedBy: string;
	completedAt: string;
}

export interface TaskBoard {
	mode: 'demo' | 'mysql';
	query: string;
	status: string;
	tasks: TaskListItem[];
	summary: {
		total: number;
		open: number;
		done: number;
		assigned: number;
	};
	note: string;
}

interface TaskRow extends RowDataPacket {
	id: number;
	pc_name?: string | null;
	created_at?: Date | string | null;
	descripcion?: string | null;
	estado?: string | null;
	solicitante?: string | null;
	completed_by?: string | null;
	completed_at?: Date | string | null;
	categoria?: string | null;
	assigned_to?: string | null;
	fuero?: string | null;
	prioridad?: number | null;
}

interface AdUserRow extends RowDataPacket {
	username: string;
	real_name?: string | null;
	fuero?: string | null;
}

function normalize(value: string) {
	return value
		.trim()
		.toLowerCase()
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '');
}

function usernameFromRequester(value: string) {
	const trimmed = value.trim();
	if (!trimmed) return '';
	return trimmed.split(/[\\/]/).at(-1)?.trim().toLowerCase() ?? trimmed.toLowerCase();
}

function dateToIso(value: Date | string | null | undefined) {
	if (!value) return '';
	const date = new Date(value);
	return Number.isNaN(date.getTime()) ? String(value) : date.toISOString();
}

export function requesterLabelForTask(task: TaskRequesterSeed, adUsers: TaskAdUser[]) {
	const requester = task.requester.trim();
	const requesterUsername = usernameFromRequester(requester);
	const requesterName = normalize(requester);
	const match = adUsers.find((user) => {
		return (
			user.username.toLowerCase() === requesterUsername ||
			normalize(user.realName) === requesterName
		);
	});
	const name = match?.realName || requester || 'Sin solicitante';
	const fuero = match?.fuero || task.fuero;
	return fuero ? `${name} (${fuero})` : name;
}

function summarize(tasks: TaskListItem[]) {
	return {
		total: tasks.length,
		open: tasks.filter((task) => ['Pendiente', 'Asignada'].includes(task.status)).length,
		done: tasks.filter((task) => ['Hecha', 'resuelto'].includes(task.status)).length,
		assigned: tasks.filter((task) => task.status === 'Asignada').length
	};
}

function rowToTask(row: TaskRow, adUsers: TaskAdUser[]): TaskListItem {
	const requester = row.solicitante ?? '';
	const fuero = row.fuero ?? '';
	return {
		id: row.id,
		pcName: row.pc_name ?? 'PC Generica',
		createdAt: dateToIso(row.created_at),
		description: row.descripcion ?? '',
		status: row.estado ?? 'Pendiente',
		requester,
		requesterLabel: requesterLabelForTask({ requester, fuero }, adUsers),
		fuero,
		category: row.categoria ?? '',
		assignedTo: row.assigned_to ?? '',
		priority: Number(row.prioridad ?? 0),
		completedBy: row.completed_by ?? '',
		completedAt: dateToIso(row.completed_at)
	};
}

export function demoTaskBoard(query = '', status = ''): TaskBoard {
	const adUsers = [{ username: 'gustavo.m', realName: 'Gustavo Mock AD', fuero: 'Sistemas' }];
	const tasks = [
		rowToTask(
			{
				id: 1,
				pc_name: 'JCC1-PC01',
				created_at: '2026-08-25T10:00:00.000Z',
				descripcion: 'Revisar impresora compartida',
				estado: 'Pendiente',
				solicitante: 'DOMINIO\\gustavo.m',
				categoria: 'Impresoras',
				assigned_to: 'Gustavo',
				fuero: '',
				prioridad: 2
			} as TaskRow,
			adUsers
		),
		rowToTask(
			{
				id: 2,
				pc_name: 'PC Generica',
				created_at: '2026-08-24T11:00:00.000Z',
				descripcion: 'Cambio de teclado',
				estado: 'Hecha',
				solicitante: 'Andrea Gomez',
				categoria: 'Hardware',
				assigned_to: 'Rita',
				fuero: 'Recursos Humanos',
				prioridad: 1
			} as TaskRow,
			adUsers
		)
	].filter((task) => {
		const queryMatch =
			!query ||
			normalize(`${task.pcName} ${task.description} ${task.requesterLabel}`).includes(
				normalize(query)
			);
		const statusMatch = !status || task.status === status;
		return queryMatch && statusMatch;
	});

	return {
		mode: 'demo',
		query,
		status,
		tasks,
		summary: summarize(tasks),
		note: 'Sin .env local: tareas demo, no se consulto MySQL.'
	};
}

export async function loadTaskBoard({
	query = '',
	status = '',
	limit = 80
}: {
	query?: string;
	status?: string;
	limit?: number;
} = {}): Promise<TaskBoard> {
	const trimmedQuery = query.trim();
	const trimmedStatus = status.trim();
	if (!appConfig.MYSQL_PASSWORD) return demoTaskBoard(trimmedQuery, trimmedStatus);

	const pool = getMysqlPool();
	const [adRows] = await pool.query<AdUserRow[]>(
		'SELECT username, real_name, fuero FROM ad_users ORDER BY real_name, username'
	);
	const adUsers = adRows.map((row) => ({
		username: row.username,
		realName: row.real_name ?? row.username,
		fuero: row.fuero ?? ''
	}));
	const likeQuery = `%${trimmedQuery}%`;
	const [taskRows] = await pool.query<TaskRow[]>(
		`
		SELECT
			id, pc_name, created_at, descripcion, estado, solicitante, completed_by,
			completed_at, categoria, assigned_to, fuero, prioridad
		FROM tasks
		WHERE (? = '' OR estado = ?)
		  AND (
			? = ''
			OR pc_name LIKE ?
			OR descripcion LIKE ?
			OR solicitante LIKE ?
			OR categoria LIKE ?
			OR assigned_to LIKE ?
		  )
		ORDER BY
			CASE estado
				WHEN 'Pendiente' THEN 0
				WHEN 'Asignada' THEN 1
				ELSE 2
			END,
			created_at DESC
		LIMIT ?
		`,
		[
			trimmedStatus,
			trimmedStatus,
			trimmedQuery,
			likeQuery,
			likeQuery,
			likeQuery,
			likeQuery,
			likeQuery,
			limit
		]
	);
	const tasks = taskRows.map((row) => rowToTask(row, adUsers));

	return {
		mode: 'mysql',
		query: trimmedQuery,
		status: trimmedStatus,
		tasks,
		summary: summarize(tasks),
		note: appConfig.MYSQL_READ_ONLY
			? 'MySQL conectado en modo lectura.'
			: 'MySQL conectado con escritura habilitada por configuracion.'
	};
}
