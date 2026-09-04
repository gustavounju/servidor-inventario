package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.armado.EstadoOrdenArmado;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.GuardarComponenteOrdenCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.GuardarOrdenArmadoCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoComponenteNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoComponenteSinStockException;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoNoEncontradaException;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.ComponenteDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.StockComponenteNoDisponibleException;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.StockComponenteNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.StockComponenteNoReservadoException;
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
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/v1")
public class OrdenArmadoController {

	private static final String MODULO_ORDENES = "ORDENES_ARMADO";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final OrdenArmadoService ordenArmadoService;

	public OrdenArmadoController(AuthorizationService authorizationService, OrdenArmadoService ordenArmadoService) {
		this.authorizationService = authorizationService;
		this.ordenArmadoService = ordenArmadoService;
	}

	@GetMapping("/equipos/{equipoId}/ordenes-armado")
	public List<OrdenArmadoDetalle> listar(@AuthenticationPrincipal UserDetails userDetails, @PathVariable Long equipoId) {
		exigirPermiso(userDetails, PERMISO_VER);
		return ordenArmadoService.listarPorEquipo(equipoId);
	}

	@PostMapping("/equipos/{equipoId}/ordenes-armado")
	@ResponseStatus(HttpStatus.CREATED)
	public OrdenArmadoDetalle crear(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId,
			@Valid @RequestBody GuardarOrdenArmadoRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return ordenArmadoService.crear(equipoId, request.toCommand());
	}

	@PostMapping("/ordenes-armado/{ordenId}/componentes")
	@ResponseStatus(HttpStatus.CREATED)
	public ComponenteDetalle agregarComponente(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenId,
			@Valid @RequestBody GuardarComponenteOrdenRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return ordenArmadoService.agregarComponenteEsperado(ordenId, request.toCommand());
	}

	@PostMapping("/ordenes-armado/componentes/{ordenComponenteId}/confirmar-salida-stock")
	public ComponenteDetalle confirmarSalidaStock(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenComponenteId) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return ordenArmadoService.confirmarSalidaStock(ordenComponenteId);
	}

	@org.springframework.web.bind.annotation.DeleteMapping("/ordenes-armado/{ordenId}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenId) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		ordenArmadoService.eliminar(ordenId);
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_ORDENES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar ordenes de armado.");
		}
	}

	@ExceptionHandler({EquipoNoEncontradoException.class, OrdenArmadoNoEncontradaException.class,
			OrdenArmadoComponenteNoEncontradoException.class,
			StockComponenteNoEncontradoException.class})
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	@ExceptionHandler({StockComponenteNoDisponibleException.class, StockComponenteNoReservadoException.class,
			OrdenArmadoComponenteSinStockException.class})
	@ResponseStatus(HttpStatus.CONFLICT)
	void noDisponible() {
	}

	public record GuardarOrdenArmadoRequest(
			@NotNull EstadoOrdenArmado estado,
			@NotBlank @Size(max = 255) String descripcion,
			@Size(max = 500) String observaciones) {

		private GuardarOrdenArmadoCommand toCommand() {
			return new GuardarOrdenArmadoCommand(estado, descripcion, observaciones);
		}
	}

	public record GuardarComponenteOrdenRequest(
			Long stockComponenteId,
			@NotNull TipoComponente tipo,
			@NotBlank @Size(max = 255) String descripcion,
			@Size(max = 120) String marca,
			@Size(max = 180) String modelo,
			@Size(max = 180) String serial,
			@Size(max = 120) String capacidad,
			@Size(max = 120) String ubicacion,
			@Size(max = 500) String observaciones,
			@Size(max = 80) String remito,
			@Size(max = 80) String ordenCompra,
			@Size(max = 150) String proveedor) {

		private GuardarComponenteOrdenCommand toCommand() {
			return new GuardarComponenteOrdenCommand(
					stockComponenteId, tipo, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones, remito, ordenCompra, proveedor);
		}
	}
}
