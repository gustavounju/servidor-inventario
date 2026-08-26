import type {
	ComponentFamily,
	EquipmentDiscrepancy,
	EquipmentTelemetry,
	ReconcileEquipmentInput,
	ReconciledComponent,
	ReconciledEquipmentDetail,
	RegisteredComponent
} from './types';

const PLACEHOLDER_SERIALS = new Set([
	'',
	'N/A',
	'SIN S/N',
	'SIN N/S',
	'NONE',
	'NULL',
	'0',
	'00000000',
	'SERIAL',
	'SERIALNUMBER',
	'SERIAL NUMBER'
]);

function isRealSerial(value: string | null | undefined) {
	return !PLACEHOLDER_SERIALS.has(
		String(value ?? '')
			.trim()
			.toUpperCase()
	);
}

function normalizeIdentity(value: string | null | undefined) {
	return String(value ?? '')
		.toUpperCase()
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.replace(/(?:\[|\()\s*(SN|S\/N|SERIAL|UUID)\s*:\s*[^\])]+(?:\]|\))/gi, ' ')
		.replace(/\b\d+(?:\.\d+)?\s*GB\b/gi, ' ')
		.replace(/[^A-Z0-9]+/g, ' ')
		.trim()
		.replace(/\s+/g, ' ');
}

function componentFamily(componentType: string | null | undefined): ComponentFamily {
	const value = normalizeIdentity(componentType);
	if (value.includes('MONITOR') || value.includes('PANTALLA')) return 'monitor';
	if (value.includes('DISCO') || value.includes('SSD') || value.includes('HDD')) return 'storage';
	if (value.includes('PROCESADOR') || value.includes('CPU') || value.includes('MICRO'))
		return 'processor';
	if (value.includes('RAM') || value.includes('MEMORIA')) return 'memory';
	if (value.includes('MOTHER') || value.includes('PLACA MADRE')) return 'motherboard';
	return 'other';
}

function splitConcatenatedSerialEntries(value: string) {
	const serialTag = /(?:\[|\()\s*(?:SN|S\/N|SERIAL|UUID)\s*:\s*[^\])]+(?:\]|\))/gi;
	const matches = [...value.matchAll(serialTag)];
	if (matches.length <= 1) return [value.trim()].filter(Boolean);

	const entries: string[] = [];
	let start = 0;
	for (let index = 0; index < matches.length; index += 1) {
		const match = matches[index];
		const end = Number(match.index) + match[0].length;
		if (index < matches.length - 1) {
			entries.push(value.slice(start, end).trim());
			start = end;
		} else {
			entries.push(value.slice(start).trim());
		}
	}

	return entries.filter(Boolean);
}

function extractSerial(value: string) {
	const match = value.match(/(?:\[|\()\s*(?:SN|S\/N|SERIAL|UUID)\s*:\s*([^\])]+)(?:\]|\))/i);
	return match?.[1]?.trim() ?? '';
}

function extractLabel(value: string) {
	return value.replace(/(?:\[|\()\s*(?:SN|S\/N|SERIAL|UUID)\s*:\s*[^\])]+(?:\]|\))/gi, '').trim();
}

function splitHardwareEntries(rawValue: string | null | undefined) {
	const value = String(rawValue ?? '').trim();
	if (!value || ['N/A', 'NONE', 'SIN REPORTE DE SCRIPT'].includes(value.toUpperCase())) return [];

	return value
		.replace(/\r?\n/g, '|')
		.replace(/;/g, '|')
		.split('|')
		.flatMap((part) => splitConcatenatedSerialEntries(part))
		.map((part) => part.trim())
		.filter(Boolean);
}

function telemetryComponents(telemetry: EquipmentTelemetry, family: 'monitor' | 'storage') {
	const rawEntries = splitHardwareEntries(
		family === 'monitor' ? telemetry.monitors : telemetry.diskModels
	);
	const result: ReconciledComponent[] = [];
	const seenSerials = new Set<string>();
	const seenIdentitiesWithSerial = new Set<string>();
	const seenModelOnlyIdentities = new Set<string>();

	for (const entry of rawEntries) {
		const serial = extractSerial(entry);
		const serialKey = serial.toUpperCase();
		const label = extractLabel(entry) || (family === 'monitor' ? 'Monitor' : 'Disco');
		const identity = normalizeIdentity(label);

		if (isRealSerial(serial)) {
			if (seenSerials.has(serialKey)) continue;
			seenSerials.add(serialKey);
			if (identity) seenIdentitiesWithSerial.add(identity);
		} else {
			if (
				!identity ||
				seenIdentitiesWithSerial.has(identity) ||
				seenModelOnlyIdentities.has(identity)
			) {
				continue;
			}
			seenModelOnlyIdentities.add(identity);
		}

		result.push({
			family,
			label,
			serialNumber: isRealSerial(serial) ? serial : 'Sin S/N',
			source: 'telemetry',
			inActa: true,
			inTelemetry: true,
			inRegistry: false
		});
	}

	return result;
}

function registeredFamilyComponents(components: RegisteredComponent[], family: ComponentFamily) {
	return components.filter((component) => componentFamily(component.componentType) === family);
}

function mergeRegistered(
	telemetryItems: ReconciledComponent[],
	registeredItems: RegisteredComponent[],
	family: 'monitor' | 'storage',
	discrepancies: EquipmentDiscrepancy[]
) {
	const merged = telemetryItems.map((item) => ({ ...item }));

	for (const registered of registeredItems) {
		const registeredSerial = String(registered.serialNumber ?? '').trim();
		const registeredSerialKey = registeredSerial.toUpperCase();
		const registeredLabel = String(registered.brandModel ?? registered.componentType).trim();
		const registeredIdentity = normalizeIdentity(registeredLabel);
		const match = merged.find((item) => {
			const itemSerialKey = item.serialNumber.toUpperCase();
			if (isRealSerial(registeredSerial) && itemSerialKey === registeredSerialKey) return true;
			return registeredIdentity && normalizeIdentity(item.label) === registeredIdentity;
		});

		if (match) {
			match.source = 'merged';
			match.inRegistry = true;
			match.label = registeredLabel || match.label;
			if (isRealSerial(registeredSerial)) match.serialNumber = registeredSerial;
			continue;
		}

		merged.push({
			family,
			label: registeredLabel || (family === 'monitor' ? 'Monitor' : 'Disco'),
			serialNumber: isRealSerial(registeredSerial) ? registeredSerial : 'Sin S/N',
			source: 'registered',
			inActa: true,
			inTelemetry: false,
			inRegistry: true
		});
		discrepancies.push({
			severity: 'warning',
			componentFamily: family,
			message: `Componente patrimonial sin coincidencia WMI: ${registeredLabel} (${isRealSerial(registeredSerial) ? registeredSerial : 'Sin S/N'})`
		});
	}

	return merged;
}

export function reconcileEquipment(input: ReconcileEquipmentInput): ReconciledEquipmentDetail {
	const discrepancies: EquipmentDiscrepancy[] = [];
	const monitorTelemetry = telemetryComponents(input.telemetry, 'monitor');
	const storageTelemetry = telemetryComponents(input.telemetry, 'storage');

	const monitors = mergeRegistered(
		monitorTelemetry,
		registeredFamilyComponents(input.registeredComponents, 'monitor'),
		'monitor',
		discrepancies
	);
	const storage = mergeRegistered(
		storageTelemetry,
		registeredFamilyComponents(input.registeredComponents, 'storage'),
		'storage',
		discrepancies
	);

	return {
		pcName: input.pcName,
		user: input.user ?? {},
		monitors,
		storage,
		actaItems: [...monitors, ...storage].filter((item) => item.inActa),
		discrepancies
	};
}
