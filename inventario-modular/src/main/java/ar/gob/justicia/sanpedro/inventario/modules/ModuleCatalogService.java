package ar.gob.justicia.sanpedro.inventario.modules;

import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class ModuleCatalogService {

	private static final List<ModuleDefinition> INITIAL_MODULES = List.of(
			new ModuleDefinition("EQUIPOS", "Equipos", "Inventario tecnico de PCs y puestos."),
			new ModuleDefinition("ACTAS", "Actas", "Actas de entrega y constancias imprimibles."),
			new ModuleDefinition("MUEBLES", "Muebles", "Registro de mobiliario y bienes no informaticos."),
			new ModuleDefinition("PATRIMONIO", "Patrimonio", "Control patrimonial y gemelos digitales."),
			new ModuleDefinition("STOCK", "Stock", "Recepcion, reserva y asignacion de componentes."),
			new ModuleDefinition("COMPONENTES", "Componentes", "Componentes internos y perifericos asociados."),
			new ModuleDefinition("USUARIOS", "Usuarios", "Usuarios, roles y permisos del sistema."),
			new ModuleDefinition("REPORTES", "Reportes", "Consultas, exportaciones y reportes operativos."),
			new ModuleDefinition("TAREAS", "Tareas", "Solicitudes y trabajos tecnicos."));

	public List<ModuleDefinition> listModules() {
		return INITIAL_MODULES;
	}
}
