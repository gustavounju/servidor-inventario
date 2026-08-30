package ar.gob.justicia.sanpedro.inventario.modules;

import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/modules")
class ModuleController {

	private final ModuleCatalogService moduleCatalogService;

	ModuleController(ModuleCatalogService moduleCatalogService) {
		this.moduleCatalogService = moduleCatalogService;
	}

	@GetMapping
	Map<String, List<ModuleDefinition>> listModules() {
		return Map.of("data", moduleCatalogService.listModules());
	}
}
