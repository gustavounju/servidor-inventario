package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.EstadoUbicacion;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.TipoUbicacion;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.GuardarUbicacionCommand;
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
public class UbicacionPageController {

	private static final String MODULO_UBICACIONES = "UBICACIONES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final UbicacionService ubicacionService;
	private final ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService;

	public UbicacionPageController(AuthorizationService authorizationService, UbicacionService ubicacionService,
			ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService) {
		this.authorizationService = authorizationService;
		this.ubicacionService = ubicacionService;
		this.fueroService = fueroService;
	}

	@GetMapping("/admin/ubicaciones")
	public String ubicaciones(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) TipoUbicacion tipo,
			@RequestParam(required = false) EstadoUbicacion estado,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, new UbicacionForm(), query, tipo, estado);
		model.addAttribute("creado", "1".equals(creado));
		return "admin/ubicaciones";
	}

	@PostMapping("/admin/ubicaciones")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("ubicacionForm") UbicacionForm ubicacionForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, ubicacionForm, null, null, null);
			return "admin/ubicaciones";
		}
		ubicacionService.crear(ubicacionForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ubicaciones";
	}

	@PostMapping("/admin/ubicaciones/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("ubicacionForm") UbicacionForm ubicacionForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, ubicacionForm, null, null, null);
			return "admin/ubicaciones";
		}
		ubicacionService.actualizar(id, ubicacionForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/ubicaciones";
	}

	@PostMapping("/admin/ubicaciones/{id}/eliminar")
	public String eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		ubicacionService.eliminar(id);
		redirectAttributes.addFlashAttribute("eliminado", true);
		return "redirect:/admin/ubicaciones";
	}

	private void prepararModelo(Model model, UserDetails userDetails, UbicacionForm ubicacionForm, String query,
			TipoUbicacion tipo, EstadoUbicacion estado) {
		model.addAttribute("ubicaciones", ubicacionService.buscar(query, tipo, estado));
		model.addAttribute("ubicacionForm", ubicacionForm);
		model.addAttribute("tiposUbicacion", TipoUbicacion.values());
		model.addAttribute("estadosUbicacion", EstadoUbicacion.values());
		model.addAttribute("filtroQuery", query);
		model.addAttribute("filtroTipo", tipo);
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("fuerosDisponibles", fueroService.listarFueros());
		model.addAttribute("puedeEditarUbicaciones",
				authorizationService.tienePermiso(userDetails, MODULO_UBICACIONES, PERMISO_EDITAR));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_UBICACIONES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar ubicaciones.");
		}
	}

	public static class UbicacionForm {

		@NotBlank
		@Size(max = 80)
		private String codigo;

		@NotBlank
		@Size(max = 180)
		private String nombre;

		@NotNull
		private TipoUbicacion tipo = TipoUbicacion.OFICINA;

		@Size(max = 120)
		private String fuero;

		@Size(max = 120)
		private String responsable;

		@Size(max = 120)
		private String edificio;

		@Size(max = 40)
		private String piso;

		@NotNull
		private EstadoUbicacion estado = EstadoUbicacion.ACTIVA;

		@Size(max = 500)
		private String observaciones;

		private boolean activo = true;

		GuardarUbicacionCommand toCommand() {
			return new GuardarUbicacionCommand(codigo, nombre, tipo, fuero, responsable, edificio, piso, estado,
					observaciones, activo);
		}

		public String getCodigo() { return codigo; }
		public void setCodigo(String codigo) { this.codigo = codigo; }
		public String getNombre() { return nombre; }
		public void setNombre(String nombre) { this.nombre = nombre; }
		public TipoUbicacion getTipo() { return tipo; }
		public void setTipo(TipoUbicacion tipo) { this.tipo = tipo; }
		public String getFuero() { return fuero; }
		public void setFuero(String fuero) { this.fuero = fuero; }
		public String getResponsable() { return responsable; }
		public void setResponsable(String responsable) { this.responsable = responsable; }
		public String getEdificio() { return edificio; }
		public void setEdificio(String edificio) { this.edificio = edificio; }
		public String getPiso() { return piso; }
		public void setPiso(String piso) { this.piso = piso; }
		public EstadoUbicacion getEstado() { return estado; }
		public void setEstado(EstadoUbicacion estado) { this.estado = estado; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
		public boolean isActivo() { return activo; }
		public void setActivo(boolean activo) { this.activo = activo; }
	}
}
