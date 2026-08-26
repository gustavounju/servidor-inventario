import { appConfig } from './config';
import { getMysqlPool } from './db';
import { reconcileEquipment } from '$lib/inventory/reconcile';
import type { ReconciledEquipmentDetail, RegisteredComponent } from '$lib/inventory/types';
import type { RowDataPacket } from 'mysql2';

interface PcRow extends RowDataPacket {
	pc_name?: string;
	last_user?: string | null;
	fuero?: string | null;
	monitors?: string | null;
	disk_models?: string | null;
	os_name?: string | null;
	ip_address?: string | null;
	last_report?: Date | string | null;
	processor?: string | null;
	motherboard_model?: string | null;
	ram_gb?: number | string | null;
	office_version?: string | null;
	validation_status?: string | null;
}

interface ComponentRow extends RowDataPacket {
	component_type?: string | null;
	brand_model?: string | null;
	serial_number?: string | null;
	invoice_number?: string | null;
	oc_number?: string | null;
	supplier?: string | null;
}

export function demoEquipmentDetail(pcName: string): ReconciledEquipmentDetail {
	return reconcileEquipment({
		pcName,
		user: { name: 'Demo Sistemas', fuero: 'Civil' },
		telemetry: {
			osName: 'Windows 11 Pro',
			ipAddress: '192.168.1.100',
			lastReport: '2026-08-25T10:00:00.000Z',
			monitors: 'Philips Philips 241V8 (SN: ZA1418003190) LG 19EN33 (SN: LG19123456)',
			diskModels:
				'KINGSTON SA400S37240G (224GB) [SN: 50026B7785247C4D] ST500DM002-1BD142 (466GB) [SN: Z3T4ABCDE]',
			processor: 'Intel Core i5',
			motherboardModel: 'ASUS PRIME',
			ramGb: 16,
			officeVersion: 'Microsoft Office 2021',
			validationStatus: 'demo'
		},
		registeredComponents: [
			{
				componentType: 'Monitor',
				brandModel: 'Philips Philips 241V8',
				serialNumber: 'ZA1418003190'
			}
		]
	});
}

function rowToRegisteredComponent(row: ComponentRow): RegisteredComponent {
	return {
		componentType: row.component_type ?? 'Otro',
		brandModel: row.brand_model,
		serialNumber: row.serial_number,
		invoiceNumber: row.invoice_number,
		ocNumber: row.oc_number,
		supplier: row.supplier
	};
}

export async function loadEquipmentDetail(pcName: string) {
	if (!appConfig.MYSQL_PASSWORD) {
		return {
			mode: 'demo' as const,
			detail: demoEquipmentDetail(pcName),
			note: 'Sin .env local: mostrando datos demo, no se consulto MySQL.'
		};
	}

	const pool = getMysqlPool();
	const [pcRows] = await pool.query<PcRow[]>(
		`
		SELECT
			pc_name, last_user, fuero, monitors, disk_models, os_name, ip_address, last_report,
			processor, motherboard_model, ram_gb, office_version, validation_status
		FROM pcs
		WHERE LOWER(TRIM(pc_name)) = LOWER(TRIM(?))
		LIMIT 1
		`,
		[pcName]
	);

	const pc = pcRows[0];
	if (!pc) {
		return {
			mode: 'not_found' as const,
			detail: demoEquipmentDetail(pcName),
			note: `No se encontro ${pcName} en MySQL.`
		};
	}

	const [componentRows] = await pool.query<ComponentRow[]>(
		`
		SELECT component_type, brand_model, serial_number, invoice_number, oc_number, supplier
		FROM components
		WHERE LOWER(TRIM(assigned_pc)) = LOWER(TRIM(?))
		  AND (status IS NULL OR status NOT IN ('Retirado', 'Scrap', 'Stock'))
		ORDER BY component_type, brand_model
		`,
		[pcName]
	);

	return {
		mode: 'mysql' as const,
		detail: reconcileEquipment({
			pcName: pc.pc_name ?? pcName,
			user: { name: pc.last_user ?? '', fuero: pc.fuero ?? '' },
			telemetry: {
				osName: pc.os_name,
				ipAddress: pc.ip_address,
				lastReport: pc.last_report,
				monitors: pc.monitors,
				diskModels: pc.disk_models,
				processor: pc.processor,
				motherboardModel: pc.motherboard_model,
				ramGb: pc.ram_gb,
				officeVersion: pc.office_version,
				validationStatus: pc.validation_status
			},
			registeredComponents: componentRows.map(rowToRegisteredComponent)
		}),
		note: appConfig.MYSQL_READ_ONLY
			? 'MySQL conectado en modo lectura.'
			: 'MySQL conectado con escritura habilitada por configuracion.'
	};
}
