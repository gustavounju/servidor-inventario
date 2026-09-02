package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService.UsuarioActual;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

@ControllerAdvice
public class AdminNavModelAdvice {

	private final AuthorizationService authorizationService;

	public AdminNavModelAdvice(AuthorizationService authorizationService) {
		this.authorizationService = authorizationService;
	}

	@ModelAttribute("currentUser")
	public UsuarioActual currentUser(@AuthenticationPrincipal UserDetails userDetails) {
		if (userDetails == null) {
			return null;
		}
		return authorizationService.obtenerUsuarioActual(userDetails);
	}

	@ModelAttribute("displayName")
	public String displayName(@AuthenticationPrincipal UserDetails userDetails) {
		if (userDetails == null) {
			return "";
		}
		UsuarioActual u = authorizationService.obtenerUsuarioActual(userDetails);
		return u != null ? u.nombreVisible() : "";
	}

	@ModelAttribute("username")
	public String username(@AuthenticationPrincipal UserDetails userDetails) {
		if (userDetails == null) {
			return "";
		}
		return userDetails.getUsername();
	}

	@ModelAttribute("fuero")
	public String fuero(@AuthenticationPrincipal UserDetails userDetails) {
		if (userDetails == null) {
			return "";
		}
		UsuarioActual u = authorizationService.obtenerUsuarioActual(userDetails);
		return u != null ? u.fuero() : "";
	}

	@ModelAttribute("canViewEquipos")
	public boolean canViewEquipos(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "EQUIPOS", "VER");
	}

	@ModelAttribute("canViewDashboardDiferencias")
	public boolean canViewDashboardDiferencias(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "COMPONENTES", "VER");
	}

	@ModelAttribute("canViewStock")
	public boolean canViewStock(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "STOCK", "VER");
	}

	@ModelAttribute("canViewOrdenesArmado")
	public boolean canViewOrdenesArmado(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "ORDENES_ARMADO", "VER");
	}

	@ModelAttribute("canViewMuebles")
	public boolean canViewMuebles(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "MUEBLES", "VER");
	}

	@ModelAttribute("canViewUbicaciones")
	public boolean canViewUbicaciones(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "UBICACIONES", "VER");
	}

	@ModelAttribute("canViewPatrimonio")
	public boolean canViewPatrimonio(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "PATRIMONIO", "VER");
	}

	@ModelAttribute("canViewActas")
	public boolean canViewActas(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "ACTAS", "VER");
	}

	@ModelAttribute("canViewReportes")
	public boolean canViewReportes(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "REPORTES", "VER");
	}

	@ModelAttribute("canViewAuditoria")
	public boolean canViewAuditoria(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "AUDITORIA", "VER");
	}

	@ModelAttribute("canViewTareas")
	public boolean canViewTareas(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "TAREAS", "VER");
	}

	@ModelAttribute("canManageUsers")
	public boolean canManageUsers(@AuthenticationPrincipal UserDetails userDetails) {
		return userDetails != null && authorizationService.tienePermiso(userDetails, "USUARIOS", "ADMINISTRAR");
	}
}
