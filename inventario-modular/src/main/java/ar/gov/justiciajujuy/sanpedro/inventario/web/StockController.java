package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.EstadoStockComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.GuardarStockComponenteCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.StockComponenteDetalle;
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
import org.springframework.web.bind.annotation.DeleteMapping;
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
@RequestMapping("/api/v1/stock/componentes")
public class StockController {

	private static final String MODULO_STOCK = "STOCK";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final StockService stockService;

	public StockController(AuthorizationService authorizationService, StockService stockService) {
		this.authorizationService = authorizationService;
		this.stockService = stockService;
	}

	@GetMapping
	public List<StockComponenteDetalle> listar(@AuthenticationPrincipal UserDetails userDetails) {
		exigirPermiso(userDetails, PERMISO_VER);
		return stockService.listarDisponiblesYActivos();
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public StockComponenteDetalle crear(
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @RequestBody GuardarStockComponenteRequest request) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		return stockService.crear(request.toCommand());
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		stockService.eliminar(id);
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_STOCK, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar stock.");
		}
	}

	@ExceptionHandler(StockComponenteNoEncontradoException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	void noEncontrado() {
	}

	@ExceptionHandler({StockComponenteNoDisponibleException.class, StockComponenteNoReservadoException.class})
	@ResponseStatus(HttpStatus.CONFLICT)
	void noDisponible() {
	}

	public record GuardarStockComponenteRequest(
			@NotNull TipoComponente tipo,
			@NotNull EstadoStockComponente estado,
			@NotBlank @Size(max = 255) String descripcion,
			@Size(max = 120) String marca,
			@Size(max = 180) String modelo,
			@Size(max = 180) String serial,
			@Size(max = 120) String capacidad,
			@Size(max = 80) String remito,
			@Size(max = 80) String ordenCompra,
			@Size(max = 150) String proveedor,
			@Size(max = 120) String ubicacion,
			@Size(max = 500) String observaciones,
			boolean activo) {

		private GuardarStockComponenteCommand toCommand() {
			return new GuardarStockComponenteCommand(
					tipo, estado, descripcion, marca, modelo, serial, capacidad, remito, ordenCompra, proveedor, ubicacion, observaciones, activo);
		}
	}
}
