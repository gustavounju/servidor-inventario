package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.EstadoBienPatrimonial;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.GuardarBienPatrimonialCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.data.domain.Pageable;
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
public class PatrimonioPageController {

	private static final String MODULO_PATRIMONIO = "PATRIMONIO";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final PatrimonioService patrimonioService;
	private final EquipoRepository equipoRepository;
	private final UbicacionService ubicacionService;
	private final ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService;

	public PatrimonioPageController(AuthorizationService authorizationService, PatrimonioService patrimonioService,
			EquipoRepository equipoRepository, UbicacionService ubicacionService,
			ar.gov.justiciajujuy.sanpedro.inventario.equipos.FueroService fueroService) {
		this.authorizationService = authorizationService;
		this.patrimonioService = patrimonioService;
		this.equipoRepository = equipoRepository;
		this.ubicacionService = ubicacionService;
		this.fueroService = fueroService;
	}

	@GetMapping("/admin/patrimonio")
	public String patrimonio(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) EstadoBienPatrimonial estado,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, new PatrimonioForm(), query, estado);
		model.addAttribute("creado", "1".equals(creado));
		return "admin/patrimonio";
	}

	@PostMapping("/admin/patrimonio/bienes")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("patrimonioForm") PatrimonioForm patrimonioForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, patrimonioForm, null, null);
			return "admin/patrimonio";
		}
		patrimonioService.crear(patrimonioForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/patrimonio";
	}

	@PostMapping("/admin/patrimonio/bienes/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("patrimonioForm") PatrimonioForm patrimonioForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, patrimonioForm, null, null);
			return "admin/patrimonio";
		}
		patrimonioService.actualizar(id, patrimonioForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/patrimonio";
	}

	private void prepararModelo(Model model, UserDetails userDetails, PatrimonioForm patrimonioForm,
			String query, EstadoBienPatrimonial estado) {
		var bienes = patrimonioService.buscar(query, estado);
		long enUsoCount = bienes.stream().filter(b -> b.estado() == EstadoBienPatrimonial.EN_USO).count();
		long enDepositoCount = bienes.stream().filter(b -> b.estado() == EstadoBienPatrimonial.EN_DEPOSITO).count();
		long vinculadosCount = bienes.stream().filter(b -> b.equipoId() != null).count();

		model.addAttribute("bienes", bienes);
		model.addAttribute("totalBienes", bienes.size());
		model.addAttribute("enUsoCount", enUsoCount);
		model.addAttribute("enDepositoCount", enDepositoCount);
		model.addAttribute("vinculadosCount", vinculadosCount);
		model.addAttribute("patrimonioForm", patrimonioForm);
		model.addAttribute("equipos", equipoRepository.buscar(null, Pageable.unpaged()).getContent());
		model.addAttribute("estadosPatrimonio", EstadoBienPatrimonial.values());
		model.addAttribute("ubicacionesActivas", ubicacionService.activas());
		model.addAttribute("filtroQuery", query);
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("fuerosDisponibles", fueroService.listarFueros());
		model.addAttribute("puedeEditarPatrimonio", authorizationService.tienePermiso(userDetails, MODULO_PATRIMONIO, PERMISO_EDITAR));
		model.addAttribute("puedeVerActas", authorizationService.tienePermiso(userDetails, "ACTAS", PERMISO_VER));
		model.addAttribute("puedeVerEquipos", authorizationService.tienePermiso(userDetails, "EQUIPOS", PERMISO_VER));
		model.addAttribute("puedeVerReportes", authorizationService.tienePermiso(userDetails, "REPORTES", "VER"));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_PATRIMONIO, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar patrimonio.");
		}
	}

	public static class PatrimonioForm {

		@NotBlank
		@Size(max = 80)
		private String numeroPatrimonial;

		@NotBlank
		@Size(max = 80)
		private String categoria;

		@NotBlank
		@Size(max = 255)
		private String descripcion;

		@Size(max = 180)
		private String ubicacion;

		@Size(max = 120)
		private String fuero;

		@Size(max = 120)
		private String custodio;

		@NotNull
		private EstadoBienPatrimonial estado = EstadoBienPatrimonial.EN_USO;

		private Long equipoId;

		@Size(max = 500)
		private String observaciones;

		private boolean activo = true;

		GuardarBienPatrimonialCommand toCommand() {
			return new GuardarBienPatrimonialCommand(numeroPatrimonial, categoria, descripcion, ubicacion, fuero,
					custodio, estado, equipoId, observaciones, activo);
		}

		public String getNumeroPatrimonial() { return numeroPatrimonial; }
		public void setNumeroPatrimonial(String numeroPatrimonial) { this.numeroPatrimonial = numeroPatrimonial; }
		public String getCategoria() { return categoria; }
		public void setCategoria(String categoria) { this.categoria = categoria; }
		public String getDescripcion() { return descripcion; }
		public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
		public String getUbicacion() { return ubicacion; }
		public void setUbicacion(String ubicacion) { this.ubicacion = ubicacion; }
		public String getFuero() { return fuero; }
		public void setFuero(String fuero) { this.fuero = fuero; }
		public String getCustodio() { return custodio; }
		public void setCustodio(String custodio) { this.custodio = custodio; }
		public EstadoBienPatrimonial getEstado() { return estado; }
		public void setEstado(EstadoBienPatrimonial estado) { this.estado = estado; }
		public Long getEquipoId() { return equipoId; }
		public void setEquipoId(Long equipoId) { this.equipoId = equipoId; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
		public boolean isActivo() { return activo; }
		public void setActivo(boolean activo) { this.activo = activo; }
	}
}
