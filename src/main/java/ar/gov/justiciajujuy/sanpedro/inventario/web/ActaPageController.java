package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.time.LocalDate;

import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.GuardarActaCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.EstadoActa;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.TipoActa;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
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
public class ActaPageController {

	private static final String MODULO_ACTAS = "ACTAS";
	private static final String PERMISO_VER = "VER";
	private static final String PERMISO_EDITAR = "EDITAR";

	private final AuthorizationService authorizationService;
	private final ActaService actaService;
	private final EquipoRepository equipoRepository;

	public ActaPageController(AuthorizationService authorizationService, ActaService actaService,
			EquipoRepository equipoRepository) {
		this.authorizationService = authorizationService;
		this.actaService = actaService;
		this.equipoRepository = equipoRepository;
	}

	@GetMapping("/admin/actas")
	public String actas(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@RequestParam(required = false) String query,
			@RequestParam(required = false) TipoActa tipo,
			@RequestParam(required = false) EstadoActa estado,
			@RequestParam(required = false) String creado) {
		exigirPermiso(userDetails, PERMISO_VER);
		prepararModelo(model, userDetails, ActaForm.nueva(actaService.proximoNumero(LocalDate.now())), query, tipo, estado);
		model.addAttribute("creado", "1".equals(creado));
		return "admin/actas";
	}

	@PostMapping("/admin/actas")
	public String crear(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@Valid @ModelAttribute("actaForm") ActaForm actaForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, actaForm, null, null, null);
			return "admin/actas";
		}
		actaService.crear(actaForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/actas";
	}

	@PostMapping("/admin/actas/{id}")
	public String actualizar(
			Model model,
			@AuthenticationPrincipal UserDetails userDetails,
			@PathVariable Long id,
			@Valid @ModelAttribute("actaForm") ActaForm actaForm,
			BindingResult bindingResult,
			RedirectAttributes redirectAttributes) {
		exigirPermiso(userDetails, PERMISO_EDITAR);
		if (bindingResult.hasErrors()) {
			prepararModelo(model, userDetails, actaForm, null, null, null);
			return "admin/actas";
		}
		actaService.actualizar(id, actaForm.toCommand());
		redirectAttributes.addAttribute("creado", "1");
		return "redirect:/admin/actas";
	}

	private void prepararModelo(Model model, UserDetails userDetails, ActaForm actaForm, String query, TipoActa tipo,
			EstadoActa estado) {
		model.addAttribute("actas", actaService.buscar(query, tipo, estado));
		model.addAttribute("actaForm", actaForm);
		model.addAttribute("tiposActa", TipoActa.values());
		model.addAttribute("estadosActa", EstadoActa.values());
		model.addAttribute("equipos", equipoRepository.findAllByOrderByNombreAsc());
		model.addAttribute("filtroQuery", query);
		model.addAttribute("filtroTipo", tipo);
		model.addAttribute("filtroEstado", estado);
		model.addAttribute("puedeEditarActas", authorizationService.tienePermiso(userDetails, MODULO_ACTAS, PERMISO_EDITAR));
	}

	private void exigirPermiso(UserDetails userDetails, String permiso) {
		if (!authorizationService.tienePermiso(userDetails, MODULO_ACTAS, permiso)) {
			throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para operar actas.");
		}
	}

	public static class ActaForm {

		@Size(max = 80)
		private String numero;

		@NotNull
		private TipoActa tipo = TipoActa.ENTREGA;

		private Long equipoId;

		private LocalDate fechaEmision = LocalDate.now();

		@NotBlank
		@Size(max = 180)
		private String destinatario;

		@Size(max = 120)
		private String responsableEntrega;

		@Size(max = 120)
		private String responsableRecepcion;

		@NotBlank
		@Size(max = 1000)
		private String detalle;

		@NotNull
		private EstadoActa estado = EstadoActa.BORRADOR;

		@Size(max = 500)
		private String observaciones;

		private boolean activo = true;

		static ActaForm nueva(String numeroSugerido) {
			ActaForm form = new ActaForm();
			form.setNumero(numeroSugerido);
			return form;
		}

		GuardarActaCommand toCommand() {
			return new GuardarActaCommand(numero, tipo, equipoId, fechaEmision, destinatario, responsableEntrega,
					responsableRecepcion, detalle, estado, observaciones, activo);
		}

		public String getNumero() { return numero; }
		public void setNumero(String numero) { this.numero = numero; }
		public TipoActa getTipo() { return tipo; }
		public void setTipo(TipoActa tipo) { this.tipo = tipo; }
		public Long getEquipoId() { return equipoId; }
		public void setEquipoId(Long equipoId) { this.equipoId = equipoId; }
		public LocalDate getFechaEmision() { return fechaEmision; }
		public void setFechaEmision(LocalDate fechaEmision) { this.fechaEmision = fechaEmision; }
		public String getDestinatario() { return destinatario; }
		public void setDestinatario(String destinatario) { this.destinatario = destinatario; }
		public String getResponsableEntrega() { return responsableEntrega; }
		public void setResponsableEntrega(String responsableEntrega) { this.responsableEntrega = responsableEntrega; }
		public String getResponsableRecepcion() { return responsableRecepcion; }
		public void setResponsableRecepcion(String responsableRecepcion) { this.responsableRecepcion = responsableRecepcion; }
		public String getDetalle() { return detalle; }
		public void setDetalle(String detalle) { this.detalle = detalle; }
		public EstadoActa getEstado() { return estado; }
		public void setEstado(EstadoActa estado) { this.estado = estado; }
		public String getObservaciones() { return observaciones; }
		public void setObservaciones(String observaciones) { this.observaciones = observaciones; }
		public boolean isActivo() { return activo; }
		public void setActivo(boolean activo) { this.activo = activo; }
	}
}
