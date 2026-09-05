package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService;
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
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService;
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

/**
 * Controlador web para la gestión de Equipos y Gemelos Digitales.
 * <p>
 * Implementa el patrón "Modern Guided Card-Based Admin Shell", soportando el circuito:
 * <ol>
 *   <li><b>Línea Base:</b> Consolidación del relevamiento inicial reportado por el script.</li>
 *   <li><b>Órdenes de Armado:</b> Consulta de intervenciones técnicas y reservas de stock.</li>
 *   <li><b>Gemelo Digital:</b> Comparación en tiempo real de hardware físico vs esperado.</li>
 * </ol>
 */
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
	private final OrdenArmadoService ordenArmadoService;
	private final ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService;
	private final StockService stockService;

	public EquipoPageController(AuthorizationService authorizationService, EquipoService equipoService,
			ComponenteService componenteService, GemeloDigitalService gemeloDigitalService,
			UbicacionService ubicacionService, InventarioViejoImportService inventarioViejoImportService,
			OrdenArmadoService ordenArmadoService,
			ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService,
			StockService stockService) {
		this.authorizationService = authorizationService;
		this.equipoService = equipoService;
		this.componenteService = componenteService;
		this.gemeloDigitalService = gemeloDigitalService;
		this.ubicacionService = ubicacionService;
		this.inventarioViejoImportService = inventarioViejoImportService;
		this.ordenArmadoService = ordenArmadoService;
		this.fueroService = fueroService;
		this.stockService = stockService;
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
		model.addAttribute("equiposConOrdenes", ordenArmadoService.listarTodas().stream()
				.map(ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoDetalle::equipoId)
				.filter(java.util.Objects::nonNull)
				.collect(java.util.stream.Collectors.toSet()));
		model.addAttribute("equiposConGemelo", componenteService.obtenerEquipoIdsConRelevamientoInicial());
		model.addAttribute("puedeEditar", authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR));
		model.addAttribute("puedeVerOrdenes", authorizationService.tienePermiso(userDetails, "ORDENES_ARMADO", PERMISO_VER));
		model.addAttribute("puedeVerStock", authorizationService.tienePermiso(userDetails, "STOCK", PERMISO_VER));
		model.addAttribute("puedeVerActas", authorizationService.tienePermiso(userDetails, "ACTAS", PERMISO_VER));
		model.addAttribute("puedeVerDiferencias", authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_VER));
		return "admin/equipos";
	}

	@org.springframework.web.bind.annotation.GetMapping("/admin/equipos/{id}")
	public String detalle(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@RequestParam(required = false) String actualizado,
			@RequestParam(required = false) String relevamiento) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_VER)) {
			throw new org.springframework.web.server.ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver equipos.");
		}
		EquipoDetalle equipo = equipoService.obtener(id);
		prepararDetalle(model, userDetails, equipo, EquipoForm.desde(equipo));
		model.addAttribute("actualizado", "1".equals(actualizado) || "relevamiento".equals(actualizado));
		model.addAttribute("relevamientoConsolidado", "relevamiento".equals(actualizado) || "1".equals(relevamiento));
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

	@PostMapping("/admin/equipos/{id}/eliminar")
	public String eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para eliminar equipos.");
		}
		equipoService.eliminar(id);
		redirectAttributes.addFlashAttribute("eliminado", true);
		return "redirect:/admin/equipos";
	}

	@PostMapping("/admin/equipos/{equipoId}/componentes/{componenteId}/eliminar")
	public String eliminarComponente(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId,
			@PathVariable Long componenteId,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para eliminar componentes.");
		}
		componenteService.eliminar(componenteId);
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/" + equipoId;
	}

	/**
	 * Permite retirar un componente físico de una máquina en taller.
	 * Soporta reingreso directo a stock de depósito (DISPONIBLE) o baja definitiva por rotura.
	 */
	@PostMapping("/admin/equipos/{equipoId}/componentes/{componenteId}/retirar")
	public String retirarComponente(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId,
			@PathVariable Long componenteId,
			@RequestParam String destino,
			@RequestParam(required = false) String motivo,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar componentes.");
		}
		componenteService.retirar(componenteId, destino, motivo);
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/" + equipoId;
	}

	/**
	 * Permite instalar de forma ágil una pieza disponible en el Stock de taller dentro de la PC.
	 * Registra el componente como ESPERADO con origen STOCK y reserva la salida física del depósito.
	 */
	@PostMapping("/admin/equipos/{equipoId}/componentes/instalar-desde-stock")
	public String instalarDesdeStock(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long equipoId,
			@RequestParam Long stockComponenteId,
			@RequestParam(required = false) String ubicacion,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para editar componentes.");
		}
		componenteService.instalarDesdeStock(equipoId, stockComponenteId, ubicacion);
		redirectAttributes.addAttribute("actualizado", "1");
		return "redirect:/admin/equipos/" + equipoId;
	}

	/**
	 * Inicia de forma ágil una PC en el Taller de Informática en un solo paso:
	 * crea el equipo con código autogenerado (ej. ARMADO-001) o ingresado,
	 * crea inmediatamente su primera Orden de Armado directamente EN TALLER (EN_ARMADO),
	 * y redirige al técnico a la pantalla de órdenes para asociar piezas de stock.
	 */
	@PostMapping("/admin/equipos/nuevo-taller")
	public String nuevoTaller(
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String codigo,
			RedirectAttributes redirectAttributes) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para crear equipos.");
		}
		EquipoDetalle nuevo = equipoService.crearEquipoEnTaller(codigo);
		ordenArmadoService.crear(nuevo.id(), new ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.GuardarOrdenArmadoCommand(
				ar.gov.justiciajujuy.sanpedro.inventario.armado.EstadoOrdenArmado.EN_ARMADO,
				"Armado y ensamblado de equipo en taller",
				"Orden inicial generada automáticamente al iniciar PC en taller."));
		redirectAttributes.addAttribute("equipoId", nuevo.id());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ordenes-armado";
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
		boolean puedeVerOrdenes = authorizationService.tienePermiso(userDetails, "ORDENES_ARMADO", PERMISO_VER);
		var listaComponentes = puedeVerComponentes ? componenteService.listarPorEquipo(equipo.id()) : java.util.List.<ComponenteService.ComponenteDetalle>of();
		var comparaciones = puedeVerComponentes ? gemeloDigitalService.compararEquipo(equipo.id()) : java.util.List.<GemeloDigitalService.ComparacionComponente>of();
		boolean tieneRelevamientoInicial = listaComponentes.stream()
				.anyMatch(c -> c.origen() == OrigenComponente.RELEVAMIENTO_INICIAL);
		long diferenciasCount = comparaciones.stream()
				.filter(c -> c.resultado() != EstadoComparacion.COINCIDE)
				.count();
		var ordenes = puedeVerOrdenes ? ordenArmadoService.listarPorEquipo(equipo.id()) : java.util.List.<ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoDetalle>of();

		BrujulaEquipo brujula = calcularBrujula(equipo, listaComponentes, tieneRelevamientoInicial, diferenciasCount, ordenes);

		model.addAttribute("equipo", equipo);
		model.addAttribute("equipoForm", equipoForm);
		model.addAttribute("puedeEditar", authorizationService.tienePermiso(userDetails, MODULO_EQUIPOS, PERMISO_EDITAR));
		model.addAttribute("puedeVerComponentes", puedeVerComponentes);
		model.addAttribute("puedeEditarComponentes", authorizationService.tienePermiso(userDetails, MODULO_COMPONENTES, PERMISO_EDITAR));
		model.addAttribute("componentes", listaComponentes);
		model.addAttribute("comparacionGemelo", comparaciones);
		model.addAttribute("tieneRelevamientoInicial", tieneRelevamientoInicial);
		model.addAttribute("diferenciasCount", diferenciasCount);
		model.addAttribute("puedeVerOrdenes", puedeVerOrdenes);
		model.addAttribute("ordenesArmado", ordenes);
		model.addAttribute("brujula", brujula);
		model.addAttribute("componenteForm", new ComponenteForm());
		model.addAttribute("tiposComponente", TipoComponente.values());
		model.addAttribute("origenesComponente", OrigenComponente.values());
		model.addAttribute("estadosComparacion", EstadoComparacion.values());
		model.addAttribute("ubicacionesActivas", ubicacionService.activas());
		model.addAttribute("fuerosDisponibles", fueroService.listarFueros());
		model.addAttribute("stockDisponibles", stockService.listarDisponiblesYActivos().stream()
				.filter(s -> "DISPONIBLE".equals(s.estado().name()))
				.toList());
		model.addAttribute("actualizado", false);
		model.addAttribute("relevamientoConsolidado", false);
	}

	public record BrujulaEquipo(
			String origenCodigo,
			String origenEtiqueta,
			String origenBadgeClass,
			String origenDetalle,
			String semaforoCodigo,
			String semaforoEtiqueta,
			String semaforoBadgeClass,
			String semaforoDetalle,
			String pasoSiguienteTitulo,
			String pasoSiguienteDescripcion,
			String pasoSiguienteAccionTexto,
			String pasoSiguienteAccionTipo,
			String pasoSiguienteEnlace) {
	}

	private BrujulaEquipo calcularBrujula(
			EquipoDetalle equipo,
			java.util.List<ComponenteService.ComponenteDetalle> componentes,
			boolean tieneRelevamientoInicial,
			long diferenciasCount,
			java.util.List<ar.gov.justiciajujuy.sanpedro.inventario.armado.OrdenArmadoService.OrdenArmadoDetalle> ordenes) {

		// 1. Origen del equipo
		String origenCodigo;
		String origenEtiqueta;
		String origenBadgeClass;
		String origenDetalle;
		if (equipo.ultimoReporteEn() != null) {
			origenCodigo = "OFICINA";
			origenEtiqueta = "🚀 Sumado via Script";
			origenBadgeClass = "is-authorized";
			if (!ordenes.isEmpty()) {
				origenDetalle = "Equipo sumado e inventariado vía script de relevamiento. Cuenta con " + ordenes.size() + " orden(es) técnica(s) en taller.";
			} else {
				origenDetalle = "Equipo sumado e inventariado directamente vía script en la máquina cliente.";
			}
		} else if (!ordenes.isEmpty()) {
			origenCodigo = "TALLER";
			origenEtiqueta = "🔧 Armado en el Taller";
			origenBadgeClass = "is-authorized";
			origenDetalle = "Equipo armado y preparado en taller técnico (" + ordenes.size() + " orden(es) registrada(s)). Pendiente de traslado e inventario inicial via script.";
		} else {
			origenCodigo = "MANUAL";
			origenEtiqueta = "📝 Registro Manual";
			origenBadgeClass = "is-pending";
			origenDetalle = "Alta en sistema. Aún no ejecutó el script de inventario ni tiene órdenes de taller.";
		}

		// 2. Semáforo del Gemelo Digital
		String semaforoCodigo;
		String semaforoEtiqueta;
		String semaforoBadgeClass;
		String semaforoDetalle;
		if (equipo.ultimoReporteEn() == null && componentes.isEmpty()) {
			semaforoCodigo = "PENDIENTE_SCRIPT";
			semaforoEtiqueta = "🟡 Esperando Script Inicial";
			semaforoBadgeClass = "is-pending";
			semaforoDetalle = "La máquina todavía no reportó su hardware. Se requiere ejecutar el script en el equipo cliente.";
		} else if (equipo.ultimoReporteEn() != null && !tieneRelevamientoInicial && ordenes.isEmpty()) {
			semaforoCodigo = "RELEVAMIENTO_PENDIENTE";
			semaforoEtiqueta = "🟡 Script se comunicó con éxito (Falta registrar Gemelo)";
			semaforoBadgeClass = "is-pending";
			semaforoDetalle = "El script se comunicó exitosamente con el servidor. Falta registrar estos componentes como el Gemelo Digital oficial.";
		} else if (diferenciasCount > 0) {
			semaforoCodigo = "DIFERENCIAS";
			semaforoEtiqueta = "🔴 " + diferenciasCount + " Discrepancia(s) en Gemelo";
			semaforoBadgeClass = "is-pending";
			semaforoDetalle = "Existen diferencias entre el Gemelo Digital oficial y lo detectado por el script en vivo.";
		} else {
			semaforoCodigo = "SINCRONIZADO";
			semaforoEtiqueta = "🟢 Gemelo Sincronizado (100% Coincide)";
			semaforoBadgeClass = "is-authorized";
			semaforoDetalle = "El hardware físico detectado coincide al 100% con el Gemelo Digital oficial.";
		}

		// 3. Próximo Paso Sugerido (Acción recomendada)
		String pasoTitulo;
		String pasoDesc;
		String pasoAccionTexto;
		String pasoAccionTipo;
		String pasoEnlace;

		if (equipo.ultimoReporteEn() == null) {
			pasoTitulo = "Paso 1: Ejecutar script de inventario en la PC";
			pasoDesc = "Para generar el gemelo digital de esta PC, ejecuta el script en el equipo cliente.";
			pasoAccionTexto = "📋 Copiar Comando PowerShell";
			pasoAccionTipo = "COPIAR_SCRIPT";
			pasoEnlace = "";
		} else if (equipo.ultimoReporteEn() != null && !tieneRelevamientoInicial) {
			pasoTitulo = "Paso 2: Registrar como Gemelo Digital Oficial";
			pasoDesc = "El hardware real fue detectado por el script. Confirma estos componentes como el Gemelo Digital oficial para fijar la línea base del equipo.";
			pasoAccionTexto = "✅ Registrar como Gemelo Digital Oficial";
			pasoAccionTipo = "CONSOLIDAR";
			pasoEnlace = "";
		} else if (diferenciasCount > 0) {
			pasoTitulo = "Paso 3: Auditar discrepancias de componentes";
			pasoDesc = "Hay componentes físicos que no coinciden con la orden de armado o el relevamiento inicial.";
			pasoAccionTexto = "🔍 Ver Comparación en Gemelo";
			pasoAccionTipo = "VER_GEMELO";
			pasoEnlace = "gemelo";
		} else if (equipo.ubicacion() == null || equipo.ubicacion().isBlank() || equipo.ultimoUsuario() == null || equipo.ultimoUsuario().isBlank()) {
			pasoTitulo = "Paso 4: Asignar Juzgado y Responsable";
			pasoDesc = "El hardware está sincronizado. Completa la oficina física y el agente responsable del equipo.";
			pasoAccionTexto = "🏢 Asignar Ubicación y Usuario";
			pasoAccionTipo = "EDITAR_UBICACION";
			pasoEnlace = "editar";
		} else {
			pasoTitulo = "Paso 5: Equipo verificado y operativo";
			pasoDesc = "El equipo está en regla con su gemelo digital y datos completos. Puedes generar el acta formal de entrega o movimiento.";
			pasoAccionTexto = "📋 Generar Acta de Entrega / Movimiento";
			pasoAccionTipo = "CREAR_ACTA";
			pasoEnlace = "/admin/actas";
		}

		return new BrujulaEquipo(
				origenCodigo,
				origenEtiqueta,
				origenBadgeClass,
				origenDetalle,
				semaforoCodigo,
				semaforoEtiqueta,
				semaforoBadgeClass,
				semaforoDetalle,
				pasoTitulo,
				pasoDesc,
				pasoAccionTexto,
				pasoAccionTipo,
				pasoEnlace);
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
		redirectAttributes.addAttribute("relevamiento", "1");
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

		@Size(max = 80)
		private String remito;

		@Size(max = 80)
		private String ordenCompra;

		@Size(max = 150)
		private String proveedor;

		GuardarComponenteCommand toCommand() {
			return new GuardarComponenteCommand(tipo, origen, estadoComparacion, descripcion, marca, modelo, serial, capacidad, remito, ordenCompra, proveedor, ubicacion, observaciones, activo);
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

		public String getRemito() {
			return remito;
		}

		public void setRemito(String remito) {
			this.remito = remito;
		}

		public String getOrdenCompra() {
			return ordenCompra;
		}

		public void setOrdenCompra(String ordenCompra) {
			this.ordenCompra = ordenCompra;
		}

		public String getProveedor() {
			return proveedor;
		}

		public void setProveedor(String proveedor) {
			this.proveedor = proveedor;
		}
	}
}
