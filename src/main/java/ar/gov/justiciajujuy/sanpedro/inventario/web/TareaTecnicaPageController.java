package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.stream.Collectors;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService.DominioUsuarios;
import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService.UsuarioDominio;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.UsuarioManagementService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.EstadoTareaTecnica;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.PrioridadTareaTecnica;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.AgregarComentarioTareaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.CambiarEstadoTareaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.GuardarTareaTecnicaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.TareaComentarioDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.TareaTecnicaDetalle;
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
public class TareaTecnicaPageController {

	private static final String MODULO_TAREAS = "TAREAS";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final TareaTecnicaService tareaTecnicaService;
	private final EquipoRepository equipoRepository;
	private final ActiveDirectoryDomainService activeDirectoryDomainService;
	private final UsuarioManagementService usuarioManagementService;
	private final FueroService fueroService;

	public TareaTecnicaPageController(
			AuthorizationService authorizationService,
			TareaTecnicaService tareaTecnicaService,
			EquipoRepository equipoRepository,
			ActiveDirectoryDomainService activeDirectoryDomainService,
			UsuarioManagementService usuarioManagementService,
			FueroService fueroService) {
		this.authorizationService = authorizationService;
		this.tareaTecnicaService = tareaTecnicaService;
		this.equipoRepository = equipoRepository;
		this.activeDirectoryDomainService = activeDirectoryDomainService;
		this.usuarioManagementService = usuarioManagementService;
		this.fueroService = fueroService;
	}

	@GetMapping("/admin/tareas")
	public String tareas(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) EstadoTareaTecnica estado,
			@RequestParam(required = false) Long equipoId,
			@RequestParam(required = false) String responsable,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, new TareaForm(), estado, equipoId, responsable);
		model.addAttribute("creado", "1".equals(creado));
		return "admin/tareas";
	}

	@PostMapping("/admin/tareas")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("tareaForm") TareaForm tareaForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		tareaForm.aplicarReglaResponsable(userDetails.getUsername(), authorizationService.puedeAdministrarUsuarios(userDetails));
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, tareaForm, null, null, null);
			return "admin/tareas";
		}
		tareaTecnicaService.crear(tareaForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/tareas";
	}

	@PostMapping("/admin/tareas/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("tareaForm") TareaForm tareaForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		exigirTareaPropiaOAdministrador(userDetails, id);
		tareaForm.aplicarReglaResponsable(userDetails.getUsername(), authorizationService.puedeAdministrarUsuarios(userDetails));
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, tareaForm, null, null, null);
			return "admin/tareas";
		}
		tareaTecnicaService.actualizar(id, tareaForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/tareas";
	}

	@PostMapping("/admin/tareas/{id}/tomar")
	public String tomar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		tareaTecnicaService.tomar(id, userDetails.getUsername());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/tareas";
	}

	@PostMapping("/admin/tareas/{id}/estado")
	public String cambiarEstado(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@RequestParam EstadoTareaTecnica estado,
			@RequestParam(required = false) String observacionesCierre,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		exigirTareaPropiaOAdministrador(userDetails, id);
		tareaTecnicaService.cambiarEstado(id, new CambiarEstadoTareaCommand(estado, observacionesCierre));
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/tareas";
	}

	@PostMapping("/admin/tareas/{id}/eliminar")
	public String eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		exigirTareaPropiaOAdministrador(userDetails, id);
		tareaTecnicaService.eliminar(id);
		redirectAttributes.addFlashAttribute("eliminado", true);
		return "redirect:/admin/tareas";
	}

	@PostMapping("/admin/tareas/{id}/comentarios")
	public String comentar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@RequestParam @NotBlank @Size(max = 1000) String comentario,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		exigirTareaPropiaOAdministrador(userDetails, id);
		tareaTecnicaService.comentar(id, new AgregarComentarioTareaCommand(userDetails.getUsername(), comentario));
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/tareas";
	}

	private void prepararModelo(Model model, UserDetails userDetails, TareaForm tareaForm,
			EstadoTareaTecnica estado, Long equipoId, String responsable) {
		List<TareaTecnicaDetalle> tareas = tareaTecnicaService.buscar(estado, equipoId, responsable);
		Map<Long, List<TareaComentarioDetalle>> comentariosPorTarea = tareas.stream()
				.collect(Collectors.toMap(TareaTecnicaDetalle::id, tarea -> tareaTecnicaService.comentarios(tarea.id())));
		model.addAttribute("tareas", tareas);
		model.addAttribute("comentariosPorTarea", comentariosPorTarea);
		model.addAttribute("tareaForm", tareaForm);
		model.addAttribute("equipos", equipoRepository.buscar(null, org.springframework.data.domain.Pageable.unpaged()).getContent().stream()
				.filter(equipo -> !TareaTecnicaService.EQUIPO_GENERICO_NOMBRE.equalsIgnoreCase(equipo.getNombre()))
				.toList());
		model.addAttribute("equipoGenericoId", equipoRepository.findByNombreIgnoreCase(TareaTecnicaService.EQUIPO_GENERICO_NOMBRE)
				.map(ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo::getId)
				.orElse(null));
		model.addAttribute("estadosTarea", EstadoTareaTecnica.values());
		model.addAttribute("prioridadesTarea", PrioridadTareaTecnica.values());
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("filtroEquipoId", equipoId);
		model.addAttribute("filtroResponsable", responsable);
		boolean puedeEditarTareas = authorizationService.tienePermiso(userDetails, MODULO_TAREAS, PERMISO_EDITAR);
		boolean puedeAsignarResponsable = authorizationService.puedeAdministrarUsuarios(userDetails);
		List<UsuarioDominio> solicitantes = solicitantesParaTareas();
		model.addAttribute("puedeEditarTareas", puedeEditarTareas);
		model.addAttribute("puedeAsignarResponsable", puedeAsignarResponsable);
		model.addAttribute("usuarioActual", userDetails.getUsername());
		model.addAttribute("solicitantes", solicitantes);
		model.addAttribute("fuerosDisponibles", fuerosParaTareas(solicitantes));
		model.addAttribute("tecnicosAsignables", usuarioManagementService.listarTecnicosAsignables());
	}

	private List<String> fuerosParaTareas(List<UsuarioDominio> solicitantes) {
		TreeSet<String> fueros = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
		fueros.addAll(fueroService.listarFueros());
		solicitantes.stream()
				.map(UsuarioDominio::fuero)
				.filter(org.springframework.util.StringUtils::hasText)
				.map(String::trim)
				.forEach(fueros::add);
		return List.copyOf(fueros);
	}

	private List<UsuarioDominio> solicitantesParaTareas() {
		DominioUsuarios usuariosDominio = activeDirectoryDomainService.listarUsuariosParaTareas();
		if (usuariosDominio.disponible()) {
			return usuariosDominio.usuarios();
		}
		return usuarioManagementService.listarUsuariosActivosNoAdministrativos().stream()
				.map(usuario -> new UsuarioDominio(usuario.username(), usuario.nombreVisible(), usuario.fuero()))
				.toList();
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_TAREAS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar tareas tecnicas.");
		}
	}

	private void exigirTareaPropiaOAdministrador(UserDetails userDetails, Long tareaId) {
		if (authorizationService.puedeAdministrarUsuarios(userDetails)) {
			return;
		}
		TareaTecnicaDetalle tarea = tareaTecnicaService.obtener(tareaId);
		if (tarea.responsable() == null || !tarea.responsable().equalsIgnoreCase(userDetails.getUsername())) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "La tarea debe estar tomada por el tecnico en sesion.");
		}
	}

	public static class TareaForm {

		private Long equipoId;

		@NotBlank
		@Size(max = 180)
		private String titulo;

		@Size(max = 1000)
		private String descripcion;

		@NotBlank
		@Size(max = 120)
		private String solicitanteUsername;

		@NotBlank
		@Size(max = 180)
		private String solicitanteNombre;

		@NotBlank
		@Size(max = 120)
		private String solicitanteFuero;

		@NotNull
		private PrioridadTareaTecnica prioridad = PrioridadTareaTecnica.MEDIA;

		@Size(max = 120)
		private String responsable;

		GuardarTareaTecnicaCommand toCommand() {
			return new GuardarTareaTecnicaCommand(
					equipoId,
					titulo,
					descripcion,
					solicitanteUsername,
					solicitanteNombre,
					solicitanteFuero,
					prioridad,
					responsable,
					null);
		}

		void aplicarReglaResponsable(String usernameActual, boolean puedeAsignarResponsable) {
			if (!puedeAsignarResponsable) {
				this.responsable = usernameActual;
			}
		}

		public Long getEquipoId() { return equipoId; }
		public void setEquipoId(Long equipoId) { this.equipoId = equipoId; }
		public String getTitulo() { return titulo; }
		public void setTitulo(String titulo) { this.titulo = titulo; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public String getSolicitanteUsername() { return solicitanteUsername; }
		public void setSolicitanteUsername(String solicitanteUsername) { this.solicitanteUsername = solicitanteUsername; }
		public String getSolicitanteNombre() { return solicitanteNombre; }
		public void setSolicitanteNombre(String solicitanteNombre) { this.solicitanteNombre = solicitanteNombre; }
		public String getSolicitanteFuero() { return solicitanteFuero; }
		public void setSolicitanteFuero(String solicitanteFuero) { this.solicitanteFuero = solicitanteFuero; }
		public PrioridadTareaTecnica getPrioridad() { return prioridad; }
		public void setPrioridad(PrioridadTareaTecnica prioridad) { this.prioridad = prioridad; }
		public String getResponsable() { return responsable; }
		public void setResponsable(String responsable) { this.responsable = responsable; }
	}
}
