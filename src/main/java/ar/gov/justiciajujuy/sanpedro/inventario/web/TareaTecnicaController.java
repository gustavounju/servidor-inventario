package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.EstadoTareaTecnica;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.PrioridadTareaTecnica;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.CambiarEstadoTareaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.GuardarTareaTecnicaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.TareaTecnicaDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.TareaTecnicaNoEncontradaException;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/tareas-tecnicas")
public class TareaTecnicaController {

	private static final String MODULO_TAREAS = "TAREAS";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final TareaTecnicaService tareaTecnicaService;

	public TareaTecnicaController(AuthorizationService authorizationService, TareaTecnicaService tareaTecnicaService) {
		this.authorizationService = authorizationService;
		this.tareaTecnicaService = tareaTecnicaService;
	}

	@GetMapping
	public List<TareaTecnicaDetalle> listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) EstadoTareaTecnica estado,
			@RequestParam(required = false) Long equipoId,
			@RequestParam(required = false) String responsable) {
		exigirPermiso(userDetails, PERMISO_VER);
		return tareaTecnicaService.buscar(estado, equipoId, responsable);
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public TareaTecnicaDetalle crear(
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarTareaTecnicaRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return tareaTecnicaService.crear(request.toCommand());
	}

	@PutMapping("/{id}")
	public TareaTecnicaDetalle actualizar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @RequestBody GuardarTareaTecnicaRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return tareaTecnicaService.actualizar(id, request.toCommand());
	}

	@PatchMapping("/{id}/estado")
	public TareaTecnicaDetalle cambiarEstado(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @RequestBody CambiarEstadoTareaRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return tareaTecnicaService.cambiarEstado(id, request.toCommand());
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_TAREAS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar tareas tecnicas.");
		}
	}

	@ExceptionHandler({TareaTecnicaNoEncontradaException.class, EquipoNoEncontradoException.class})
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	public record GuardarTareaTecnicaRequest(
			Long equipoId,
			@NotBlank @Size(max = 180) String titulo,
			@Size(max = 1000) String descripcion,
			PrioridadTareaTecnica prioridad,
			@Size(max = 120) String responsable) {

		private GuardarTareaTecnicaCommand toCommand() {
			return new GuardarTareaTecnicaCommand(equipoId, titulo, descripcion, prioridad, responsable);
		}
	}

	public record CambiarEstadoTareaRequest(
			@NotNull EstadoTareaTecnica estado,
			@Size(max = 1000) String observacionesCierre) {

		private CambiarEstadoTareaCommand toCommand() {
			return new CambiarEstadoTareaCommand(estado, observacionesCierre);
		}
	}
}
