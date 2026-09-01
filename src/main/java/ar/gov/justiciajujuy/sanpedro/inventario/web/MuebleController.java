package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.muebles.EstadoMueble;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.GuardarMuebleCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.MuebleDuplicadoException;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.MuebleDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.MuebleNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1/muebles")
public class MuebleController {

	private static final String MODULO_MUEBLES = "MUEBLES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final MuebleService muebleService;

	public MuebleController(AuthorizationService authorizationService, MuebleService muebleService) {
		this.authorizationService = authorizationService;
		this.muebleService = muebleService;
	}

	@GetMapping
	public List<MuebleDetalle> listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) EstadoMueble estado) {
		exigirPermiso(userDetails, PERMISO_VER);
		return muebleService.buscar(query, estado);
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public MuebleDetalle crear(@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarMuebleRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return muebleService.crear(request.toCommand());
	}

	@PutMapping("/{id}")
	public MuebleDetalle actualizar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id,
			@Valid @RequestBody GuardarMuebleRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return muebleService.actualizar(id, request.toCommand());
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_MUEBLES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar muebles.");
		}
	}

	@ExceptionHandler(MuebleNoEncontradoException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	@ExceptionHandler(MuebleDuplicadoException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void duplicado() {
	}

	public record GuardarMuebleRequest(
			@NotBlank @Size(max = 80) String codigo,
			@NotBlank @Size(max = 80) String tipo,
			@NotBlank @Size(max = 255) String descripcion,
			@Size(max = 180) String ubicacion,
			@Size(max = 120) String fuero,
			@Size(max = 120) String responsable,
			EstadoMueble estado,
			@Size(max = 500) String observaciones,
			boolean activo) {

		private GuardarMuebleCommand toCommand() {
			return new GuardarMuebleCommand(codigo, tipo, descripcion, ubicacion, fuero, responsable, estado,
					observaciones, activo);
		}
	}
}
