package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.ComponenteDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.ComponenteNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.GuardarComponenteCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.EstadoComparacion;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.OrigenComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1")
public class ComponenteController {

	private static final String MODULO_COMPONENTES = "COMPONENTES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final ComponenteService componenteService;

	public ComponenteController(AuthorizationService authorizationService, ComponenteService componenteService) {
		this.authorizationService = authorizationService;
		this.componenteService = componenteService;
	}

	@GetMapping("/equipos/{equipoId}/componentes")
	public List<ComponenteDetalle> listar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long equipoId) {
		exigirPermiso(userDetails, PERMISO_VER);
		return componenteService.listarPorEquipo(equipoId);
	}

	@PostMapping("/equipos/{equipoId}/componentes")
	@ResponseStatus(HttpStatus.CREATED)
	public ComponenteDetalle crear(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId,
			@Valid @RequestBody GuardarComponenteRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return componenteService.crear(equipoId, request.toCommand());
	}

	@PostMapping("/equipos/{equipoId}/componentes/consolidar-relevamiento-inicial")
	public List<ComponenteDetalle> consolidarRelevamientoInicial(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return componenteService.consolidarRelevamientoInicial(equipoId);
	}

	@PutMapping("/componentes/{id}")
	public ComponenteDetalle actualizar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @RequestBody GuardarComponenteRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return componenteService.actualizar(id, request.toCommand());
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar componentes.");
		}
	}

	@ExceptionHandler({EquipoNoEncontradoException.class, ComponenteNoEncontradoException.class})
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	public record GuardarComponenteRequest(
			@NotNull
			TipoComponente tipo,

			@NotNull
			OrigenComponente origen,

			@NotNull
			EstadoComparacion estadoComparacion,

			@NotBlank
			@Size(max = 255)
			String descripcion,

			@Size(max = 120)
			String marca,

			@Size(max = 180)
			String modelo,

			@Size(max = 180)
			String serial,

			@Size(max = 120)
			String capacidad,

			@Size(max = 80)
			String remito,

			@Size(max = 80)
			String ordenCompra,

			@Size(max = 150)
			String proveedor,

			@Size(max = 120)
			String ubicacion,

			@Size(max = 500)
			String observaciones,

			boolean activo) {

		private GuardarComponenteCommand toCommand() {
			return new GuardarComponenteCommand(
					tipo,
					origen,
					estadoComparacion,
					descripcion,
					marca,
					modelo,
					serial,
					capacidad,
					remito,
					ordenCompra,
					proveedor,
					ubicacion,
					observaciones,
					activo);
		}
	}
}
