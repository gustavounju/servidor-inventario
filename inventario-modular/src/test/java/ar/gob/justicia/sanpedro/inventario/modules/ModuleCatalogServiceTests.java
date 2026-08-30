package ar.gob.justicia.sanpedro.inventario.modules;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.Test;

class ModuleCatalogServiceTests {

	private final ModuleCatalogService service = new ModuleCatalogService();

	@Test
	void returnsStableInitialModuleCatalog() {
		List<ModuleDefinition> modules = service.listModules();

		assertThat(modules)
				.extracting(ModuleDefinition::code)
				.containsExactly(
						"EQUIPOS",
						"ACTAS",
						"MUEBLES",
						"PATRIMONIO",
						"STOCK",
						"COMPONENTES",
						"USUARIOS",
						"REPORTES",
						"TAREAS");
	}

	@Test
	void moduleCodesAreUppercaseAndUnique() {
		List<String> codes = service.listModules().stream().map(ModuleDefinition::code).toList();

		assertThat(codes).doesNotHaveDuplicates();
		assertThat(codes).allSatisfy((code) -> assertThat(code).matches("[A-Z_]+"));
	}
}
