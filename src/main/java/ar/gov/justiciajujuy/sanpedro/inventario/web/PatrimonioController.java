package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.EstadoBienPatrimonial;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.BienPatrimonialDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.BienPatrimonialDuplicadoException;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.BienPatrimonialNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.GuardarBienPatrimonialCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.DeleteMapping;
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
@RequestMapping("/api/v1/patrimonio/bienes")
public class PatrimonioController {

	private static final String MODULO_PATRIMONIO = "PATRIMONIO";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final PatrimonioService patrimonioService;

	public PatrimonioController(AuthorizationService authorizationService, PatrimonioService patrimonioService) {
		this.authorizationService = authorizationService;
		this.patrimonioService = patrimonioService;
	}

	@GetMapping
	public List<BienPatrimonialDetalle> listar(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) EstadoBienPatrimonial estado) {
		exigirPermiso(userDetails, PERMISO_VER);
		return patrimonioService.buscar(query, estado);
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public BienPatrimonialDetalle crear(@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarBienPatrimonialRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return patrimonioService.crear(request.toCommand());
	}

	@PutMapping("/{id}")
	public BienPatrimonialDetalle actualizar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id,
			@Valid @RequestBody GuardarBienPatrimonialRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return patrimonioService.actualizar(id, request.toCommand());
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void eliminar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		patrimonioService.eliminar(id);
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_PATRIMONIO, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar patrimonio.");
		}
	}

	@ExceptionHandler({BienPatrimonialNoEncontradoException.class, EquipoNoEncontradoException.class})
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	@ExceptionHandler(BienPatrimonialDuplicadoException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void duplicado() {
	}

	public record GuardarBienPatrimonialRequest(
			@NotBlank @Size(max = 80) String numeroPatrimonial,
			@NotBlank @Size(max = 80) String categoria,
			@NotBlank @Size(max = 255) String descripcion,
			@Size(max = 180) String ubicacion,
			@Size(max = 120) String fuero,
			@Size(max = 120) String custodio,
			EstadoBienPatrimonial estado,
			Long equipoId,
			@Size(max = 500) String observaciones,
			boolean activo) {

		private GuardarBienPatrimonialCommand toCommand() {
			return new GuardarBienPatrimonialCommand(numeroPatrimonial, categoria, descripcion, ubicacion, fuero,
					custodio, estado, equipoId, observaciones, activo);
		}
	}
}
