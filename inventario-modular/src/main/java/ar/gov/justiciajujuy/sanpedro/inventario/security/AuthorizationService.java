package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthorizationService {

	private final UsuarioSistemaRepository usuarioSistemaRepository;
	private final ModuloRepository moduloRepository;

	public AuthorizationService(UsuarioSistemaRepository usuarioSistemaRepository, ModuloRepository moduloRepository) {
		this.usuarioSistemaRepository = usuarioSistemaRepository;
		this.moduloRepository = moduloRepository;
	}

	@Transactional(readOnly = true)
	public UsuarioActual obtenerUsuarioActual(UserDetails userDetails) {
		String username = userDetails != null ? userDetails.getUsername() : "";
		UsuarioSistema usuarioSistema = usuarioSistemaRepository.findByUsernameIgnoreCase(username).orElse(null);
		boolean autorizado = usuarioSistema != null && usuarioSistema.isActivo();
		List<ModuloAutorizado> modulos = autorizado ? obtenerModulos(username) : List.of();

		return new UsuarioActual(
				username,
				nombreVisible(userDetails, usuarioSistema),
				fuero(userDetails, usuarioSistema),
				autorizado,
				modulos);
	}

	@Transactional(readOnly = true)
	public boolean tienePermiso(UserDetails userDetails, String moduloCodigo, String permisoCodigo) {
		if (userDetails != null && userDetails.getAuthorities().stream()
				.anyMatch(a -> a.getAuthority().equals("ROLE_MACHINE"))) {
			return "EQUIPOS".equalsIgnoreCase(moduloCodigo) &&
					("EDITAR".equalsIgnoreCase(permisoCodigo) || "VER".equalsIgnoreCase(permisoCodigo));
		}
		return obtenerUsuarioActual(userDetails).modulos().stream()
				.filter(modulo -> modulo.codigo().equalsIgnoreCase(moduloCodigo))
				.anyMatch(modulo -> modulo.permisos().stream()
						.anyMatch(permiso -> permiso.equalsIgnoreCase(permisoCodigo)));
	}

	private List<ModuloAutorizado> obtenerModulos(String username) {
		/*
		 * Agrupamos la consulta plana de SQL en objetos por modulo. Asi la API queda
		 * estable para la futura app movil y la pantalla web no necesita entender tablas.
		 */
		Map<String, ModuloAutorizadoBuilder> modulos = new LinkedHashMap<>();
		for (ModuloPermisoProjection row : moduloRepository.findAllowedModulesByUsername(username)) {
			modulos.computeIfAbsent(row.getModuloCodigo(), codigo -> new ModuloAutorizadoBuilder(
					codigo,
					row.getModuloNombre(),
					row.getModuloDescripcion(),
					row.getModuloOrden()))
				.permisos()
				.add(row.getPermisoCodigo());
		}
		return modulos.values().stream()
				.map(ModuloAutorizadoBuilder::build)
				.toList();
	}

	private String nombreVisible(UserDetails userDetails, UsuarioSistema usuarioSistema) {
		if (usuarioSistema != null) {
			return usuarioSistema.getNombreVisible();
		}
		if (userDetails instanceof ActiveDirectoryUserDetails activeDirectoryUser) {
			return activeDirectoryUser.getDisplayName();
		}
		return userDetails != null ? userDetails.getUsername() : "";
	}

	private String fuero(UserDetails userDetails, UsuarioSistema usuarioSistema) {
		if (usuarioSistema != null) {
			return usuarioSistema.getFuero();
		}
		if (userDetails instanceof ActiveDirectoryUserDetails activeDirectoryUser) {
			return activeDirectoryUser.getFuero();
		}
		return "Sin fuero informado";
	}

	public record UsuarioActual(
			String username,
			String nombreVisible,
			String fuero,
			boolean autorizado,
			List<ModuloAutorizado> modulos) {
	}

	public record ModuloAutorizado(
			String codigo,
			String nombre,
			String descripcion,
			int orden,
			List<String> permisos) {
	}

	private record ModuloAutorizadoBuilder(
			String codigo,
			String nombre,
			String descripcion,
			int orden,
			List<String> permisos) {

		private ModuloAutorizadoBuilder(String codigo, String nombre, String descripcion, int orden) {
			this(codigo, nombre, descripcion, orden, new ArrayList<>());
		}

		private ModuloAutorizado build() {
			return new ModuloAutorizado(codigo, nombre, descripcion, orden, List.copyOf(permisos));
		}
	}
}
