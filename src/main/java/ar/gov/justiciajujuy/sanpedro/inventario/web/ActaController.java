package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.time.LocalDate;
import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.ActaDuplicadaException;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.ActaDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.ActaNoEncontradaException;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.EquipoNoEncontradoParaActaException;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.GuardarActaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaPdfService;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.EstadoActa;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.TipoActa;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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
@RequestMapping("/api/v1/actas")
public class ActaController {

	private static final String MODULO_ACTAS = "ACTAS";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final ActaService actaService;
	private final ActaPdfService actaPdfService;

	public ActaController(AuthorizationService authorizationService, ActaService actaService,
			ActaPdfService actaPdfService) {
		this.authorizationService = authorizationService;
		this.actaService = actaService;
		this.actaPdfService = actaPdfService;
	}

	@GetMapping
	public List<ActaDetalle> listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) TipoActa tipo,
			@RequestParam(required = false) EstadoActa estado) {
		exigirPermiso(userDetails, PERMISO_VER);
		return actaService.buscar(query, tipo, estado);
	}

	@GetMapping("/proximo-numero")
	public ProximoNumeroActa proximoNumero(@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) LocalDate fechaEmision) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return new ProximoNumeroActa(actaService.proximoNumero(fechaEmision));
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public ActaDetalle crear(@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarActaRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return actaService.crear(request.toCommand());
	}

	@PutMapping("/{id}")
	public ActaDetalle actualizar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id,
			@Valid @RequestBody GuardarActaRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return actaService.actualizar(id, request.toCommand());
	}

	@GetMapping(value = "/{id}/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
	public ResponseEntity<byte[]> pdf(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long id) {
		exigirPermiso(userDetails, PERMISO_VER);
		ActaDetalle acta = actaService.obtener(id);
		return ResponseEntity.ok()
				.header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"acta-" + acta.numero() + ".pdf\"")
				.contentType(MediaType.APPLICATION_PDF)
				.body(actaPdfService.generar(acta));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_ACTAS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar actas.");
		}
	}

	@ExceptionHandler(ActaNoEncontradaException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrada() {
	}

	@ExceptionHandler(ActaDuplicadaException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void duplicada() {
	}

	@ExceptionHandler(EquipoNoEncontradoParaActaException.class)
	@ResponseStatus(HttpStatus.BAD_REQUEST)
	void equipoNoEncontrado() {
	}

	public record GuardarActaRequest(
			@Size(max = 80) String numero,
			TipoActa tipo,
			Long equipoId,
			LocalDate fechaEmision,
			@NotBlank @Size(max = 180) String destinatario,
			@Size(max = 120) String responsableEntrega,
			@Size(max = 120) String responsableRecepcion,
			@NotBlank @Size(max = 1000) String detalle,
			EstadoActa estado,
			@Size(max = 500) String observaciones,
			boolean activo) {

		private GuardarActaCommand toCommand() {
			return new GuardarActaCommand(numero, tipo, equipoId, fechaEmision, destinatario, responsableEntrega,
					responsableRecepcion, detalle, estado, observaciones, activo);
		}
	}

	public record ProximoNumeroActa(String numero) {
	}
}
