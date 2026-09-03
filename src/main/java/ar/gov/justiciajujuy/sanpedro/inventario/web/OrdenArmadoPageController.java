package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.HashMap;
import java.util.stream.Collectors;

import ar.gov.justiciajujuy.sanpedro.inventario.armado.EstadoOrdenArmado;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.GuardarComponenteOrdenCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.GuardarOrdenArmadoCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService;
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

/**
 * Controlador web para la gestión del flujo de Órdenes de Armado y Ensamble.
 * <p>
 * Coordina el ciclo de vida del ensamblaje técnico:
 * <ol>
 *   <li><b>Paso 1 (Plan):</b> Creación de la orden de trabajo para el equipo.</li>
 *   <li><b>Paso 2 (Reserva):</b> Asignación de componentes desde stock (estado RESERVADO).</li>
 *   <li><b>Paso 3 (Salida):</b> Confirmación física del retiro de almacén (estado ASIGNADO).</li>
 *   <li><b>Paso 4 (Gemelo):</b> Verificación de componentes esperados en el gemelo digital.</li>
 * </ol>
 */
@Controller
public class OrdenArmadoPageController {

	private static final String MODULO_ORDENES = "ORDENES_ARMADO";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final OrdenArmadoService ordenArmadoService;
	private final EquipoService equipoService;
	private final StockService stockService;

	public OrdenArmadoPageController(AuthorizationService authorizationService, OrdenArmadoService ordenArmadoService,
			EquipoService equipoService, StockService stockService) {
		this.authorizationService = authorizationService;
		this.ordenArmadoService = ordenArmadoService;
		this.equipoService = equipoService;
		this.stockService = stockService;
	}

	@GetMapping("/admin/ordenes-armado")
	public String ordenes(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) Long equipoId,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, equipoId, new OrdenForm(), new ComponenteEsperadoForm());
		model.addAttribute("creado", "1".equals(creado));
		return "admin/ordenes-armado";
	}

	@PostMapping("/admin/ordenes-armado")
	public String crearOrden(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("ordenForm") OrdenForm ordenForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, ordenForm.getEquipoId(), ordenForm, new ComponenteEsperadoForm());
			return "admin/ordenes-armado";
		}
		ordenArmadoService.crear(ordenForm.getEquipoId(), ordenForm.toCommand());
		redirectAttributes.addAttribute("equipoId", ordenForm.getEquipoId());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
	}

	@PostMapping("/admin/ordenes-armado/{ordenId}/componentes")
	public String agregarComponente(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenId,
			@RequestParam Long equipoId,
			@Valid @ModelAttribute("componenteEsperadoForm") ComponenteEsperadoForm componenteEsperadoForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, equipoId, new OrdenForm(equipoId), componenteEsperadoForm);
			return "admin/ordenes-armado";
		}
		ordenArmadoService.agregarComponenteEsperado(ordenId, componenteEsperadoForm.toCommand());
		redirectAttributes.addAttribute("equipoId", equipoId);
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
	}

	@PostMapping("/admin/ordenes-armado/{ordenId}")
	public String actualizarOrden(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenId,
			@RequestParam Long equipoId,
			@Valid @ModelAttribute("ordenForm") OrdenForm ordenForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, equipoId, ordenForm, new ComponenteEsperadoForm());
			return "admin/ordenes-armado";
		}
		ordenArmadoService.actualizar(ordenId, ordenForm.toCommand());
		redirectAttributes.addAttribute("equipoId", equipoId);
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
	}

	@PostMapping("/admin/ordenes-armado/componentes")
	public String agregarComponenteSeleccionandoOrden(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam Long equipoId,
			@Valid @ModelAttribute("componenteEsperadoForm") ComponenteEsperadoForm componenteEsperadoForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, equipoId, new OrdenForm(equipoId), componenteEsperadoForm);
			return "admin/ordenes-armado";
		}
		ordenArmadoService.agregarComponenteEsperado(componenteEsperadoForm.getOrdenId(), componenteEsperadoForm.toCommand());
		redirectAttributes.addAttribute("equipoId", equipoId);
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
	}

	@PostMapping("/admin/ordenes-armado/componentes/{ordenComponenteId}/confirmar-salida-stock")
	public String confirmarSalidaStock(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long ordenComponenteId,
			@RequestParam Long equipoId,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		ordenArmadoService.confirmarSalidaStock(ordenComponenteId);
		redirectAttributes.addAttribute("equipoId", equipoId);
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
	}

	private void prepararModelo(Model model, UserDetails userDetails, Long equipoId, OrdenForm ordenForm,
			ComponenteEsperadoForm componenteEsperadoForm) {
		var equipos = equipoService.listar(null, 0, 100).equipos();
		Long seleccionado = equipoId != null ? equipoId : (equipos.isEmpty() ? null : equipos.getFirst().id());
		if (ordenForm.getEquipoId() == null) {
			ordenForm.setEquipoId(seleccionado);
		}
		var ordenes = seleccionado != null ? ordenArmadoService.listarPorEquipo(seleccionado) : ordenArmadoService.listarTodas();
		var componentesOrden = seleccionado != null ? new HashMap<>(ordenArmadoService.listarComponentesPorEquipo(seleccionado).stream()
				.collect(Collectors.groupingBy(OrdenArmadoService.OrdenArmadoComponenteDetalle::ordenId))) : new HashMap<Long, java.util.List<OrdenArmadoService.OrdenArmadoComponenteDetalle>>();
		for (var orden : ordenes) {
			componentesOrden.putIfAbsent(orden.id(), java.util.List.of());
		}
		if (componenteEsperadoForm.getOrdenId() == null && !ordenes.isEmpty()) {
			componenteEsperadoForm.setOrdenId(ordenes.getFirst().id());
		}
		var equipoSeleccionado = seleccionado != null ? equipoService.obtener(seleccionado) : null;
		long piezasReservadas = componentesOrden.values().stream()
				.flatMap(java.util.List::stream)
				.filter(c -> c.estadoStock() != null && "RESERVADO".equals(c.estadoStock().name()))
				.count();
		long piezasAsignadas = componentesOrden.values().stream()
				.flatMap(java.util.List::stream)
				.filter(c -> c.estadoStock() != null && "ASIGNADO".equals(c.estadoStock().name()))
				.count();

		model.addAttribute("equipos", equipos);
		model.addAttribute("equipoSeleccionadoId", seleccionado);
		model.addAttribute("equipoSeleccionado", equipoSeleccionado);
		model.addAttribute("piezasReservadas", piezasReservadas);
		model.addAttribute("piezasAsignadas", piezasAsignadas);
		model.addAttribute("ordenes", ordenes);
		model.addAttribute("componentesOrden", componentesOrden);
		model.addAttribute("ordenForm", ordenForm);
		model.addAttribute("componenteEsperadoForm", componenteEsperadoForm);
		model.addAttribute("componentesStock", stockService.listarDisponiblesYActivos());
		model.addAttribute("tiposComponente", TipoComponente.values());
		model.addAttribute("estadosOrden", EstadoOrdenArmado.values());
		model.addAttribute("puedeEditarOrdenes", authorizationService.tienePermiso(userDetails, MODULO_ORDENES, PERMISO_EDITAR));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_ORDENES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar ordenes de armado.");
		}
	}

	public static class OrdenForm {

		@NotNull
		private Long equipoId;

		@NotNull
		private EstadoOrdenArmado estado = EstadoOrdenArmado.EN_ARMADO;

		@NotBlank
		@Size(max = 255)
		private String descripcion;

		@Size(max = 500)
		private String observaciones;

		public OrdenForm() {
		}

		public OrdenForm(Long equipoId) {
			this.equipoId = equipoId;
		}

		GuardarOrdenArmadoCommand toCommand() {
			return new GuardarOrdenArmadoCommand(estado, descripcion, observaciones);
		}

		public Long getEquipoId() { return equipoId; }
		public void setEquipoId(Long equipoId) { this.equipoId = equipoId; }
		public EstadoOrdenArmado getEstado() { return estado; }
		public void setEstado(EstadoOrdenArmado estado) { this.estado = estado; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
	}

	public static class ComponenteEsperadoForm {

		@NotNull
		private Long ordenId;

		private Long stockComponenteId;

		@NotNull
		private TipoComponente tipo = TipoComponente.RAM;

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

		GuardarComponenteOrdenCommand toCommand() {
			return new GuardarComponenteOrdenCommand(stockComponenteId, tipo, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones);
		}

		public Long getOrdenId() { return ordenId; }
		public void setOrdenId(Long ordenId) { this.ordenId = ordenId; }
		public Long getStockComponenteId() { return stockComponenteId; }
		public void setStockComponenteId(Long stockComponenteId) { this.stockComponenteId = stockComponenteId; }
		public TipoComponente getTipo() { return tipo; }
		public void setTipo(TipoComponente tipo) { this.tipo = tipo; }
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
	}
}
