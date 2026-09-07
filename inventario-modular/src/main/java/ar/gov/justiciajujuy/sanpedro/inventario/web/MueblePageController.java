package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.muebles.EstadoMueble;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.GuardarMuebleCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
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
public class MueblePageController {

	private static final String MODULO_MUEBLES = "MUEBLES";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final MuebleService muebleService;
	private final UbicacionService ubicacionService;
	private final ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService;

	public MueblePageController(AuthorizationService authorizationService, MuebleService muebleService,
			UbicacionService ubicacionService,
			ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService) {
		this.authorizationService = authorizationService;
		this.muebleService = muebleService;
		this.ubicacionService = ubicacionService;
		this.fueroService = fueroService;
	}

	@GetMapping("/admin/muebles")
	public String muebles(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) EstadoMueble estado,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, new MuebleForm(), query, estado);
		model.addAttribute("creado", "1".equals(creado));
		return "admin/muebles";
	}

	@PostMapping("/admin/muebles")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("muebleForm") MuebleForm muebleForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, muebleForm, null, null);
			return "admin/muebles";
		}
		muebleService.crear(muebleForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/muebles";
	}

	@PostMapping("/admin/muebles/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("muebleForm") MuebleForm muebleForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, muebleForm, null, null);
			return "admin/muebles";
		}
		muebleService.actualizar(id, muebleForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/muebles";
	}

	@PostMapping("/admin/muebles/{id}/eliminar")
	public String eliminar(
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		muebleService.eliminar(id);
		redirectAttributes.addFlashAttribute("eliminado", true);
		return "redirect:/admin/muebles";
	}

	private void prepararModelo(Model model, UserDetails userDetails, MuebleForm muebleForm, String query, EstadoMueble estado) {
		model.addAttribute("muebles", muebleService.buscar(query, estado));
		model.addAttribute("muebleForm", muebleForm);
		model.addAttribute("estadosMueble", EstadoMueble.values());
		model.addAttribute("ubicacionesActivas", ubicacionService.activas());
		model.addAttribute("fuerosDisponibles", fueroService.listarFueros());
		model.addAttribute("filtroQuery", query);
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("puedeEditarMuebles", authorizationService.tienePermiso(userDetails, MODULO_MUEBLES, PERMISO_EDITAR));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_MUEBLES, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar muebles.");
		}
	}

	public static class MuebleForm {

		@NotBlank
		@Size(max = 80)
		private String codigo;

		@NotBlank
		@Size(max = 80)
		private String tipo;

		@NotBlank
		@Size(max = 255)
		private String descripcion;

		@Size(max = 180)
		private String ubicacion;

		@Size(max = 120)
		private String fuero;

		@Size(max = 120)
		private String responsable;

		@NotNull
		private EstadoMueble estado = EstadoMueble.ACTIVO;

		@Size(max = 500)
		private String observaciones;

		private boolean activo = true;

		GuardarMuebleCommand toCommand() {
			return new GuardarMuebleCommand(codigo, tipo, descripcion, ubicacion, fuero, responsable, estado, observaciones, activo);
		}

		public String getCodigo() { return codigo; }
		public void setCodigo(String codigo) { this.codigo = codigo; }
		public String getTipo() { return tipo; }
		public void setTipo(String tipo) { this.tipo = tipo; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public String getUbicacion() { return ubicacion; }
		public void setUbicacion(String ubicacion) { this.ubicacion = ubicacion; }
		public String getFuero() { return fuero; }
		public void setFuero(String fuero) { this.fuero = fuero; }
		public String getResponsable() { return responsable; }
		public void setResponsable(String responsable) { this.responsable = responsable; }
		public EstadoMueble getEstado() { return estado; }
		public void setEstado(EstadoMueble estado) { this.estado = estado; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
		public boolean isActivo() { return activo; }
		public void setActivo(boolean activo) { this.activo = activo; }
	}
}
