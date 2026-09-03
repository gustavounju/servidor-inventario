package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.EstadoStockComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService.GuardarStockComponenteCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class StockPageController {

	private static final String MODULO_STOCK = "STOCK";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final StockService stockService;
	private final UbicacionService ubicacionService;

	public StockPageController(AuthorizationService authorizationService, StockService stockService,
			UbicacionService ubicacionService) {
		this.authorizationService = authorizationService;
		this.stockService = stockService;
		this.ubicacionService = ubicacionService;
	}

	@GetMapping("/admin/stock")
	public String stock(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, new StockForm());
		model.addAttribute("creado", "1".equals(creado));
		return "admin/stock";
	}

	@PostMapping("/admin/stock/componentes")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("stockForm") StockForm stockForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, stockForm);
			return "admin/stock";
		}
		stockService.crear(stockForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/stock";
	}

	@PostMapping("/admin/stock/componentes/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("stockForm") StockForm stockForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, stockForm);
			return "admin/stock";
		}
		stockService.actualizar(id, stockForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/stock";
	}

	private void prepararModelo(Model model, UserDetails userDetails, StockForm stockForm) {
		var componentes = stockService.listarDisponiblesYActivos();
		long disponiblesCount = componentes.stream().filter(c -> c.estado() == EstadoStockComponente.DISPONIBLE).count();
		long reservadosCount = componentes.stream().filter(c -> c.estado() == EstadoStockComponente.RESERVADO).count();
		long asignadosCount = componentes.stream().filter(c -> c.estado() == EstadoStockComponente.ASIGNADO).count();

		model.addAttribute("componentesStock", componentes);
		model.addAttribute("totalStock", componentes.size());
		model.addAttribute("disponiblesCount", disponiblesCount);
		model.addAttribute("reservadosCount", reservadosCount);
		model.addAttribute("asignadosCount", asignadosCount);
		model.addAttribute("stockForm", stockForm);
		model.addAttribute("tiposComponente", TipoComponente.values());
		model.addAttribute("estadosStock", EstadoStockComponente.values());
		model.addAttribute("ubicacionesActivas", ubicacionService.activas());
		model.addAttribute("puedeEditarStock", authorizationService.tienePermiso(userDetails, MODULO_STOCK, PERMISO_EDITAR));
		model.addAttribute("puedeVerOrdenes", authorizationService.tienePermiso(userDetails, "ORDENES_ARMADO", PERMISO_VER));
		model.addAttribute("puedeVerEquipos", authorizationService.tienePermiso(userDetails, "EQUIPOS", PERMISO_VER));
		model.addAttribute("puedeVerDiferencias", authorizationService.tienePermiso(userDetails, "COMPONENTES", PERMISO_VER));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_STOCK, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar stock.");
		}
	}

	public static class StockForm {

		@NotNull
		private TipoComponente tipo = TipoComponente.RAM;

		@NotNull
		private EstadoStockComponente estado = EstadoStockComponente.DISPONIBLE;

		@NotBlank
		@Size(max = 255)
		private String descripcion;

		@Size(max = 120)
		private String marca;

		@Size(max = 180)
		private String modelo;

		@Size(max = 180)
		private String serial;

		@Size(max = 120)
		private String capacidad;

		@Size(max = 120)
		private String ubicacion;

		@Size(max = 500)
		private String observaciones;

		private boolean activo = true;

		GuardarStockComponenteCommand toCommand() {
			return new GuardarStockComponenteCommand(tipo, estado, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones, activo);
		}

		public TipoComponente getTipo() { return tipo; }
		public void setTipo(TipoComponente tipo) { this.tipo = tipo; }
		public EstadoStockComponente getEstado() { return estado; }
		public void setEstado(EstadoStockComponente estado) { this.estado = estado; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public String getMarca() { return marca; }
		public void setMarca(String marca) { this.marca = marca; }
		public String getModelo() { return modelo; }
		public void setModelo(String modelo) { this.modelo = modelo; }
		public String getSerial() { return serial; }
		public void setSerial(String serial) { this.serial = serial; }
		public String getCapacidad() { return capacidad; }
		public void setCapacidad(String capacidad) { this.capacidad = capacidad; }
		public String getUbicacion() { return ubicacion; }
		public void setUbicacion(String ubicacion) { this.ubicacion = ubicacion; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
		public boolean isActivo() { return activo; }
		public void setActivo(boolean activo) { this.activo = activo; }
	}
}
