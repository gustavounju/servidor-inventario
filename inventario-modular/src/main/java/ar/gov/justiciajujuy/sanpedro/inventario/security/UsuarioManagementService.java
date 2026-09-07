package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.List;
import java.util.Set;
import java.util.TreeSet;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class UsuarioManagementService {

	private final UsuarioSistemaRepository usuarioSistemaRepository;
	private final RolRepository rolRepository;
	private final CredencialLocalRepository credencialLocalRepository;
	private final PasswordEncoder passwordEncoder;

	public UsuarioManagementService(
			UsuarioSistemaRepository usuarioSistemaRepository,
			RolRepository rolRepository,
			CredencialLocalRepository credencialLocalRepository,
			PasswordEncoder passwordEncoder) {
		this.usuarioSistemaRepository = usuarioSistemaRepository;
		this.rolRepository = rolRepository;
		this.credencialLocalRepository = credencialLocalRepository;
		this.passwordEncoder = passwordEncoder;
	}

	@Transactional(readOnly = true)
	public List<UsuarioResumen> listarUsuarios() {
		return usuarioSistemaRepository.findAllWithRoles().stream()
				.map(this::toResumen)
				.toList();
	}

	@Transactional(readOnly = true)
	public List<RolResumen> listarRoles() {
		return rolRepository.findAll().stream()
				.sorted(java.util.Comparator.comparing(Rol::getCodigo))
				.map(rol -> new RolResumen(
						rol.getId(),
						rol.getCodigo(),
						rol.getNombre(),
						rol.getDescripcion(),
						rol.isActivo()))
				.toList();
	}

	@Transactional
	public UsuarioResumen crearUsuario(CrearUsuarioCommand command) {
		/*
		 * El username se guarda normalizado para que `GMURAD`, `gmurad` y `Gmurad`
		 * representen a la misma cuenta de dominio dentro del inventario.
		 */
		String usernameNormalizado = normalizar(command.username());
		OrigenIdentidad origen = OrigenIdentidad.desde(command.origen());
		validarPasswordLocal(origen, command.password());
		if (usuarioSistemaRepository.existsByUsernameIgnoreCase(usernameNormalizado)) {
			throw new UsuarioDuplicadoException(usernameNormalizado);
		}

		UsuarioSistema usuario = new UsuarioSistema(
				usernameNormalizado,
				command.nombreVisible().trim(),
				command.fuero().trim(),
				origen);
		usuario.setActivo(command.activo());
		usuario.reemplazarRoles(buscarRoles(command.roles()));

		UsuarioSistema usuarioGuardado = usuarioSistemaRepository.save(usuario);
		if (origen == OrigenIdentidad.LOCAL) {
			/*
			 * La clave local nunca se guarda en texto plano. Solo queda el hash BCrypt,
			 * suficiente para que Spring Security compare futuros inicios de sesion.
			 */
			credencialLocalRepository.save(new CredencialLocal(
					usuarioGuardado,
					passwordEncoder.encode(command.password()),
					false));
		}

		return toResumen(usuarioGuardado);
	}

	@Transactional
	public UsuarioResumen autorizarUsuarioDominio(AutorizarUsuarioDominioCommand command) {
		return crearUsuario(new CrearUsuarioCommand(
				command.username(),
				command.nombreVisible(),
				command.fuero(),
				OrigenIdentidad.AD.name(),
				null,
				command.activo(),
				command.roles()));
	}

	@Transactional
	public UsuarioResumen actualizarUsuario(Long id, Set<String> roles, boolean activo) {
		UsuarioSistema usuario = usuarioSistemaRepository.findById(id)
				.orElseThrow(() -> new IllegalArgumentException("Usuario no encontrado: " + id));
		usuario.setActivo(activo);
		usuario.reemplazarRoles(buscarRoles(roles));
		return toResumen(usuarioSistemaRepository.save(usuario));
	}

	@Transactional
	public void cambiarPasswordLocal(Long id, String nuevoPassword) {
		UsuarioSistema usuario = usuarioSistemaRepository.findById(id)
				.orElseThrow(() -> new IllegalArgumentException("Usuario no encontrado: " + id));
		if (usuario.getOrigen() != OrigenIdentidad.LOCAL) {
			throw new IllegalArgumentException("Solo se puede cambiar la clave de usuarios locales.");
		}
		if (!StringUtils.hasText(nuevoPassword) || nuevoPassword.length() < 8) {
			throw new PasswordLocalRequeridoException();
		}
		CredencialLocal credencial = credencialLocalRepository.findById(id)
				.orElseGet(() -> new CredencialLocal(usuario, "", false));
		credencial.setPasswordHash(passwordEncoder.encode(nuevoPassword));
		credencialLocalRepository.save(credencial);
	}

	private void validarPasswordLocal(OrigenIdentidad origen, String password) {
		if (origen == OrigenIdentidad.LOCAL && !StringUtils.hasText(password)) {
			throw new PasswordLocalRequeridoException();
		}
		if (origen == OrigenIdentidad.LOCAL && password.length() < 8) {
			throw new PasswordLocalRequeridoException();
		}
	}

	private Set<Rol> buscarRoles(Set<String> codigos) {
		Set<String> codigosNormalizados = new TreeSet<>();
		for (String codigo : codigos) {
			codigosNormalizados.add(codigo.trim().toUpperCase());
		}

		Set<Rol> roles = rolRepository.findByCodigoInAndActivoTrue(codigosNormalizados);
		if (roles.size() != codigosNormalizados.size()) {
			throw new RolNoEncontradoException(codigosNormalizados);
		}
		return roles;
	}

	private UsuarioResumen toResumen(UsuarioSistema usuario) {
		List<String> roles = usuario.getRoles().stream()
				.map(Rol::getCodigo)
				.sorted()
				.toList();
		return new UsuarioResumen(
				usuario.getId(),
				usuario.getUsername(),
				usuario.getNombreVisible(),
				usuario.getFuero(),
				usuario.getOrigen().name(),
				usuario.isActivo(),
				credencialLocalRepository.existsByUsuarioUsernameIgnoreCase(usuario.getUsername()),
				roles);
	}

	private String normalizar(String username) {
		return username.trim().toLowerCase();
	}

	public record CrearUsuarioCommand(
			String username,
			String nombreVisible,
			String fuero,
			String origen,
			String password,
			boolean activo,
			Set<String> roles) {
	}

	public record AutorizarUsuarioDominioCommand(
			String username,
			String nombreVisible,
			String fuero,
			boolean activo,
			Set<String> roles) {
	}

	public record UsuarioResumen(
			Long id,
			String username,
			String nombreVisible,
			String fuero,
			String origen,
			boolean activo,
			boolean tieneCredencialLocal,
			List<String> roles) {
	}

	public record RolResumen(
			Long id,
			String codigo,
			String nombre,
			String descripcion,
			boolean activo) {
	}

	public static class UsuarioDuplicadoException extends RuntimeException {

		public UsuarioDuplicadoException(String username) {
			super("El usuario ya existe: " + username);
		}
	}

	public static class RolNoEncontradoException extends RuntimeException {

		public RolNoEncontradoException(Set<String> codigos) {
			super("No se encontraron todos los roles solicitados: " + codigos);
		}
	}

	public static class PasswordLocalRequeridoException extends RuntimeException {

		public PasswordLocalRequeridoException() {
			super("Los usuarios locales requieren una clave de al menos 8 caracteres.");
		}
	}
}
