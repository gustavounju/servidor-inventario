package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.GuardarComponenteCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.EstadoComparacion;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.GemeloDigitalService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.OrigenComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.ActualizarEquipoCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoDuplicadoException;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.InventarioViejoImportService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.validation.BindingResult;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import org.springframework.web.server.ResponseStatusException;

@Controller
public class EquipoPageController {

	private static final String MODULO_EQUIPOS = "EQUIPOS";
	private static final String MODULO_COMPONENTES = "COMPONENTES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final EquipoService equipoService;
	private final ComponenteService componenteService;
	private final GemeloDigitalService gemeloDigitalService;
	private final UbicacionService ubicacionService;
	private final InventarioViejoImportService inventarioViejoImportService;

	public EquipoPageController(AuthorizationService authorizationService, EquipoService equipoService,
			ComponenteService componenteService, GemeloDigitalService gemeloDigitalService,
			UbicacionService ubicacionService, InventarioViejoImportService inventarioViejoImportService) {
		this.authorizationService = authorizationService;
		this.equipoService = equipoService;
		this.componenteService = componenteService;
		this.gemeloDigitalService = gemeloDigitalService;
		this.ubicacionService = ubicacionService;
		this.inventarioViejoImportService = inventarioViejoImportService;
	}

	@GetMapping("/admin/equipos")
	public String equipos(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String q) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_VER)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver equipos.");
		}
		model.addAttribute("query", q == null ? "" : q.trim());
		model.addAttribute("equipos", equipoService.listar(q, 0, 50));
		model.addAttribute("puedeEditar", authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR));
		return "admin/equipos";
	}

	@org.springframework.web.bind.annotation.GetMapping("/admin/equipos/{id}")
	public String detalle(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@RequestParam(required = false) String actualizado) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_VER)) {
			throw new org.springframework.web.server.ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver equipos.");
		}
		EquipoDetalle equipo = equipoService.obtener(id);
		prepararDetalle(model, userDetails, equipo, EquipoForm.desde(equipo));
		model.addAttribute("actualizado", "1".equals(actualizado));
		return "admin/equipo-detalle";
	}

	@PostMapping("/admin/equipos/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("equipoForm") EquipoForm equipoForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar equipos.");
		}
		EquipoDetalle equipoActual = equipoService.obtener(id);
		if (bindingResult.hasErrors()) {
			prepararDetalle(model, userDetails, equipoActual, equipoForm);
			return "admin/equipo-detalle";
		}
		try {
			equipoService.actualizarManualmente(id, equipoForm.toCommand());
		} catch (EquipoDuplicadoException ex) {
			bindingResult.rejectValue("nombre", "duplicado", ex.getMessage());
			prepararDetalle(model, userDetails, equipoActual, equipoForm);
			return "admin/equipo-detalle";
		}
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/{id}";
	}

	@PostMapping("/admin/equipos/importar-viejo")
	public String importarInventarioViejo(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam String contenidoCsv,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar equipos.");
		}
		redirectAttributes.addFlashAttribute("importacionResultado", inventarioViejoImportService.importarCsv(contenidoCsv));
		return "redirect:/admin/equipos";
	}

	private void prepararDetalle(Model model, UserDetails userDetails, EquipoDetalle equipo, EquipoForm equipoForm) {
		boolean puedeVerComponentes = authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_VER);
		model.addAttribute("equipo", equipo);
		model.addAttribute("equipoForm", equipoForm);
		model.addAttribute("puedeEditar", authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR));
		model.addAttribute("puedeVerComponentes", puedeVerComponentes);
		model.addAttribute("puedeEditarComponentes", authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR));
		model.addAttribute("componentes", puedeVerComponentes ? componenteService.listarPorEquipo(equipo.id()) : java.util.List.of());
		model.addAttribute("comparacionGemelo", puedeVerComponentes ? gemeloDigitalService.compararEquipo(equipo.id()) : java.util.List.of());
		model.addAttribute("componenteForm", new ComponenteForm());
		model.addAttribute("tiposComponente", TipoComponente.values());
		model.addAttribute("origenesComponente", OrigenComponente.values());
		model.addAttribute("estadosComparacion", EstadoComparacion.values());
		model.addAttribute("ubicacionesActivas", ubicacionService.activas());
	}

	@PostMapping("/admin/equipos/{id}/componentes")
	public String crearComponente(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("componenteForm") ComponenteForm componenteForm,
			BindingResult bindingResult,
			Model model,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar componentes.");
		}
		EquipoDetalle equipo = equipoService.obtener(id);
		if (bindingResult.hasErrors()) {
			prepararDetalle(model, userDetails, equipo, EquipoForm.desde(equipo));
			model.addAttribute("componenteForm", componenteForm);
			return "admin/equipo-detalle";
		}
		componenteService.crear(id, componenteForm.toCommand());
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/{id}";
	}

	@PostMapping("/admin/equipos/{id}/componentes/consolidar-relevamiento-inicial")
	public String consolidarRelevamientoInicial(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar componentes.");
		}
		componenteService.consolidarRelevamientoInicial(id);
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/{id}";
	}

	public static class EquipoForm {

		@NotBlank
		@Size(max = 120)
		@Pattern(regexp = "^[a-zA-Z0-9._-]+$")
		private String nombre;

		@Size(max = 120)
		private String ultimoUsuario;

		@NotBlank
		@Size(max = 120)
		private String fuero;

		@Size(max = 180)
		private String ubicacion;

		@Size(max = 45)
		private String ip;

		@Size(max = 180)
		private String sistemaOperativo;

		@Size(max = 255)
		private String procesador;

		@Min(0)
		@Max(1048576)
		private Integer ramMb;

		@Size(max = 500)
		private String ramDetalles;

		@Size(max = 500)
		private String ramSeriales;

		@Size(max = 500)
		private String discosModelos;

		@Size(max = 500)
		private String discosSeriales;

		@Size(max = 255)
		private String motherboardModelo;

		@Size(max = 255)
		private String motherboardSerial;

		@Size(max = 500)
		private String monitores;

		@Size(max = 180)
		private String teclado;

		@Size(max = 180)
		private String mouse;

		@Size(max = 180)
		private String impresora;

		private boolean activo;

		static EquipoForm desde(EquipoDetalle equipo) {
			EquipoForm form = new EquipoForm();
			form.nombre = equipo.nombre();
			form.ultimoUsuario = equipo.ultimoUsuario();
			form.fuero = equipo.fuero();
			form.ubicacion = equipo.ubicacion();
			form.ip = equipo.ip();
			form.sistemaOperativo = equipo.sistemaOperativo();
			form.procesador = equipo.procesador();
			form.ramMb = equipo.ramMb();
			form.ramDetalles = equipo.ramDetalles();
			form.ramSeriales = equipo.ramSeriales();
			form.discosModelos = equipo.discosModelos();
			form.discosSeriales = equipo.discosSeriales();
			form.motherboardModelo = equipo.motherboardModelo();
			form.motherboardSerial = equipo.motherboardSerial();
			form.monitores = equipo.monitores();
			form.teclado = equipo.teclado();
			form.mouse = equipo.mouse();
			form.impresora = equipo.impresora();
			form.activo = equipo.activo();
			return form;
		}

		ActualizarEquipoCommand toCommand() {
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

		public String getNombre() {
			return nombre;
		}

		public void setNombre(String nombre) {
			this.nombre = nombre;
		}

		public String getUltimoUsuario() {
			return ultimoUsuario;
		}

		public void setUltimoUsuario(String ultimoUsuario) {
			this.ultimoUsuario = ultimoUsuario;
		}

		public String getFuero() {
			return fuero;
		}

		public void setFuero(String fuero) {
			this.fuero = fuero;
		}

		public String getUbicacion() {
			return ubicacion;
		}

		public void setUbicacion(String ubicacion) {
			this.ubicacion = ubicacion;
		}

		public String getIp() {
			return ip;
		}

		public void setIp(String ip) {
			this.ip = ip;
		}

		public String getSistemaOperativo() {
			return sistemaOperativo;
		}

		public void setSistemaOperativo(String sistemaOperativo) {
			this.sistemaOperativo = sistemaOperativo;
		}

		public String getProcesador() {
			return procesador;
		}

		public void setProcesador(String procesador) {
			this.procesador = procesador;
		}

		public Integer getRamMb() {
			return ramMb;
		}

		public void setRamMb(Integer ramMb) {
			this.ramMb = ramMb;
		}

		public String getRamDetalles() {
			return ramDetalles;
		}

		public void setRamDetalles(String ramDetalles) {
			this.ramDetalles = ramDetalles;
		}

		public String getRamSeriales() {
			return ramSeriales;
		}

		public void setRamSeriales(String ramSeriales) {
			this.ramSeriales = ramSeriales;
		}

		public String getDiscosModelos() {
			return discosModelos;
		}

		public void setDiscosModelos(String discosModelos) {
			this.discosModelos = discosModelos;
		}

		public String getDiscosSeriales() {
			return discosSeriales;
		}

		public void setDiscosSeriales(String discosSeriales) {
			this.discosSeriales = discosSeriales;
		}

		public String getMotherboardModelo() {
			return motherboardModelo;
		}

		public void setMotherboardModelo(String motherboardModelo) {
			this.motherboardModelo = motherboardModelo;
		}

		public String getMotherboardSerial() {
			return motherboardSerial;
		}

		public void setMotherboardSerial(String motherboardSerial) {
			this.motherboardSerial = motherboardSerial;
		}

		public String getMonitores() {
			return monitores;
		}

		public void setMonitores(String monitores) {
			this.monitores = monitores;
		}

		public String getTeclado() {
			return teclado;
		}

		public void setTeclado(String teclado) {
			this.teclado = teclado;
		}

		public String getMouse() {
			return mouse;
		}

		public void setMouse(String mouse) {
			this.mouse = mouse;
		}

		public String getImpresora() {
			return impresora;
		}

		public void setImpresora(String impresora) {
			this.impresora = impresora;
		}

		public boolean isActivo() {
			return activo;
		}

		public void setActivo(boolean activo) {
			this.activo = activo;
		}
	}

	public static class ComponenteForm {

		@NotNull
		private TipoComponente tipo = TipoComponente.RAM;

		@NotNull
		private OrigenComponente origen = OrigenComponente.MANUAL;

		@NotNull
		private EstadoComparacion estadoComparacion = EstadoComparacion.REVISAR;

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

		GuardarComponenteCommand toCommand() {
			return new GuardarComponenteCommand(tipo, origen, estadoComparacion, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones, activo);
		}

		public TipoComponente getTipo() {
			return tipo;
		}

		public void setTipo(TipoComponente tipo) {
			this.tipo = tipo;
		}

		public OrigenComponente getOrigen() {
			return origen;
		}

		public void setOrigen(OrigenComponente origen) {
			this.origen = origen;
		}

		public EstadoComparacion getEstadoComparacion() {
			return estadoComparacion;
		}

		public void setEstadoComparacion(EstadoComparacion estadoComparacion) {
			this.estadoComparacion = estadoComparacion;
		}

		public String getDescripcion() {
			return descripcion;
		}

		public void setDescripcion(String descripcion) {
			this.descripcion = descripcion;
		}

		public String getMarca() {
			return marca;
		}

		public void setMarca(String marca) {
			this.marca = marca;
		}

		public String getModelo() {
			return modelo;
		}

		public void setModelo(String modelo) {
			this.modelo = modelo;
		}

		public String getSerial() {
			return serial;
		}

		public void setSerial(String serial) {
			this.serial = serial;
		}

		public String getCapacidad() {
			return capacidad;
		}

		public void setCapacidad(String capacidad) {
			this.capacidad = capacidad;
		}

		public String getUbicacion() {
			return ubicacion;
		}

		public void setUbicacion(String ubicacion) {
			this.ubicacion = ubicacion;
		}

		public String getObservaciones() {
			return observaciones;
		}

		public void setObservaciones(String observaciones) {
			this.observaciones = observaciones;
		}

		public boolean isActivo() {
			return activo;
		}

		public void setActivo(boolean activo) {
			this.activo = activo;
		}
	}
}
