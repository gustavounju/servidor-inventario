export type ComponentFamily =
	'monitor' | 'storage' | 'processor' | 'memory' | 'motherboard' | 'other';

export type ComponentSource = 'telemetry' | 'registered' | 'merged';

export interface EquipmentUser {
	name?: string;
	fuero?: string;
}

export interface EquipmentTelemetry {
	monitors?: string | null;
	diskModels?: string | null;
	processor?: string | null;
	motherboardModel?: string | null;
	ramGb?: number | string | null;
}

export interface RegisteredComponent {
	componentType: string;
	brandModel?: string | null;
	serialNumber?: string | null;
	invoiceNumber?: string | null;
	ocNumber?: string | null;
	supplier?: string | null;
}

export interface ReconciledComponent {
	family: ComponentFamily;
	label: string;
	serialNumber: string;
	source: ComponentSource;
	inActa: boolean;
	inTelemetry: boolean;
	inRegistry: boolean;
}

export interface EquipmentDiscrepancy {
	code: 'registered_missing_in_telemetry' | 'telemetry_missing_in_registry';
	severity: 'info' | 'warning' | 'danger';
	componentFamily: ComponentFamily;
	message: string;
	recommendedAction: string;
}

export interface ReconcileEquipmentInput {
	pcName: string;
	user?: EquipmentUser;
	telemetry: EquipmentTelemetry;
	registeredComponents: RegisteredComponent[];
}

export interface ReconciledEquipmentDetail {
	pcName: string;
	user: EquipmentUser;
	monitors: ReconciledComponent[];
	storage: ReconciledComponent[];
	actaItems: ReconciledComponent[];
	discrepancies: EquipmentDiscrepancy[];
}
