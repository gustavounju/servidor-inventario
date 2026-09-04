package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ActualizarEquipoCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDuplicadoException;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoPagina;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ReporteInventarioCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.InventarioViejoImportService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.InventarioViejoImportService.ImportacionInventarioViejoResultado;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
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
@RequestMapping("/api/v1/equipos")
public class EquipoController {

	private static final String MODULO_EQUIPOS = "EQUIPOS";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final EquipoService equipoService;
	private final ComponenteService componenteService;
	private final InventarioViejoImportService inventarioViejoImportService;

	public EquipoController(AuthorizationService authorizationService, EquipoService equipoService,
			ComponenteService componenteService, InventarioViejoImportService inventarioViejoImportService) {
		this.authorizationService = authorizationService;
		this.equipoService = equipoService;
		this.componenteService = componenteService;
		this.inventarioViejoImportService = inventarioViejoImportService;
	}

	@GetMapping
	public EquipoPagina listar(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String q,
			@RequestParam(defaultValue = "0") int page,
			@RequestParam(defaultValue = "25") int pageSize) {
		exigirPermiso(userDetails, PERMISO_VER);
		return equipoService.listar(q, page, pageSize);
	}

	@GetMapping("/{id}")
	public EquipoDetalle obtener(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id) {
		exigirPermiso(userDetails, PERMISO_VER);
		return equipoService.obtener(id);
	}

	@PostMapping("/inventario")
	@ResponseStatus(HttpStatus.CREATED)
	public EquipoDetalle registrarInventario(
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody ReporteInventarioRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		ReporteInventarioCommand command = request.toCommand();
		EquipoDetalle equipo = equipoService.registrarInventario(command);
		componenteService.registrarDetectadosDesdeReporte(equipo.id(), command);
		return equipo;
	}

	@PutMapping("/{id}")
	public EquipoDetalle actualizar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @RequestBody ActualizarEquipoRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return equipoService.actualizarManualmente(id, request.toCommand());
	}

	@org.springframework.web.bind.annotation.DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		equipoService.eliminar(id);
	}

	@PostMapping(value = "/importar-viejo", consumes = {"text/csv", "text/plain"})
	public ImportacionInventarioViejoResultado importarInventarioViejo(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestBody String contenidoCsv) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return inventarioViejoImportService.importarCsv(contenidoCsv);
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar equipos.");
		}
	}

	@ExceptionHandler(EquipoNoEncontradoException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void equipoNoEncontrado() {
	}

	@ExceptionHandler(EquipoDuplicadoException.class)
	@ResponseStatus(HttpStatus.CONFLICT)
	void equipoDuplicado() {
	}

	public record ReporteInventarioRequest(
			@NotBlank
			@Size(max = 120)
			@Pattern(regexp = "^[a-zA-Z0-9._-]+$")
			String nombre,

			@Size(max = 120)
			String ultimoUsuario,

			@Size(max = 120)
			String fuero,

			@Size(max = 180)
			String ubicacion,

			@Size(max = 45)
			String ip,

			@Size(max = 180)
			String sistemaOperativo,

			@Size(max = 255)
			String procesador,

			@Min(0)
			@Max(1048576)
			Integer ramMb,

			@Size(max = 500)
			String ramDetalles,

			@Size(max = 500)
			String ramSeriales,

			@Size(max = 500)
			String discosModelos,

			@Size(max = 500)
			String discosSeriales,

			@Size(max = 255)
			String motherboardModelo,

			@Size(max = 255)
			String motherboardSerial,

			@Size(max = 500)
			String monitores,

			@Size(max = 180)
			String teclado,

			@Size(max = 180)
			String mouse,

			@Size(max = 180)
			String impresora,

			boolean activo) {

		private ReporteInventarioCommand toCommand() {
			return new ReporteInventarioCommand(
					nombre,
					ultimoUsuario,
					fuero,
					ubicacion,
					ip,
					sistemaOperativo,
					procesador,
					ramMb,
					ramDetalles,
					ramSeriales,
					discosModelos,
					discosSeriales,
					motherboardModelo,
					motherboardSerial,
					monitores,
					teclado,
					mouse,
					impresora,
					activo);
		}
	}

	public record ActualizarEquipoRequest(
			@NotBlank
			@Size(max = 120)
			@Pattern(regexp = "^[a-zA-Z0-9._-]+$")
			String nombre,

			@Size(max = 120)
			String ultimoUsuario,

			@NotBlank
			@Size(max = 120)
			String fuero,

			@Size(max = 180)
			String ubicacion,

			@Size(max = 45)
			String ip,

			@Size(max = 180)
			String sistemaOperativo,

			@Size(max = 255)
			String procesador,

			@Min(0)
			@Max(1048576)
			Integer ramMb,

			@Size(max = 500)
			String ramDetalles,

			@Size(max = 500)
			String ramSeriales,

			@Size(max = 500)
			String discosModelos,

			@Size(max = 500)
			String discosSeriales,

			@Size(max = 255)
			String motherboardModelo,

			@Size(max = 255)
			String motherboardSerial,

			@Size(max = 500)
			String monitores,

			@Size(max = 180)
			String teclado,

			@Size(max = 180)
			String mouse,

			@Size(max = 180)
			String impresora,

			boolean activo) {

		private ActualizarEquipoCommand toCommand() {
			return new ActualizarEquipoCommand(
					nombre,
					ultimoUsuario,
					fuero,
					ubicacion,
					ip,
					sistemaOperativo,
					procesador,
					ramMb,
					ramDetalles,
					ramSeriales,
					discosModelos,
					discosSeriales,
					motherboardModelo,
					motherboardSerial,
					monitores,
					teclado,
					mouse,
					impresora,
					activo);
		}
	}
}
