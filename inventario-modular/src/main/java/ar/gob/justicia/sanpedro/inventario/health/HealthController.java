package ar.gob.justicia.sanpedro.inventario.health;

import java.time.Instant;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
class HealthController {

	@GetMapping({ "/", "/api/v1/health" })
	Map<String, String> health() {
		return Map.of(
				"status", "ok",
				"service", "inventario-modular",
				"timestamp", Instant.now().toString());
	}
}
