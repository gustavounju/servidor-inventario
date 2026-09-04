package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
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

	public TareaTecnicaPageController(
			AuthorizationService authorizationService,
			TareaTecnicaService tareaTecnicaService,
			EquipoRepository equipoRepository) {
		this.authorizationService = authorizationService;
		this.tareaTecnicaService = tareaTecnicaService;
		this.equipoRepository = equipoRepository;
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
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, tareaForm, null, null, null);
			return "admin/tareas";
		}
		tareaTecnicaService.actualizar(id, tareaForm.toCommand());
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
		model.addAttribute("equipos", equipoRepository.buscar(null, org.springframework.data.domain.Pageable.unpaged()).getContent());
		model.addAttribute("estadosTarea", EstadoTareaTecnica.values());
		model.addAttribute("prioridadesTarea", PrioridadTareaTecnica.values());
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("filtroEquipoId", equipoId);
		model.addAttribute("filtroResponsable", responsable);
		model.addAttribute("puedeEditarTareas", authorizationService.tienePermiso(userDetails, MODULO_TAREAS, PERMISO_EDITAR));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_TAREAS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar tareas tecnicas.");
		}
	}

	public static class TareaForm {

		private Long equipoId;

		@NotBlank
		@Size(max = 180)
		private String titulo;

		@Size(max = 1000)
		private String descripcion;

		@NotNull
		private PrioridadTareaTecnica prioridad = PrioridadTareaTecnica.MEDIA;

		@Size(max = 120)
		private String responsable;

		GuardarTareaTecnicaCommand toCommand() {
			return new GuardarTareaTecnicaCommand(equipoId, titulo, descripcion, prioridad, responsable);
		}

		public Long getEquipoId() { return equipoId; }
		public void setEquipoId(Long equipoId) { this.equipoId = equipoId; }
		public String getTitulo() { return titulo; }
		public void setTitulo(String titulo) { this.titulo = titulo; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public PrioridadTareaTecnica getPrioridad() { return prioridad; }
		public void setPrioridad(PrioridadTareaTecnica prioridad) { this.prioridad = prioridad; }
		public String getResponsable() { return responsable; }
		public void setResponsable(String responsable) { this.responsable = responsable; }
	}
}
