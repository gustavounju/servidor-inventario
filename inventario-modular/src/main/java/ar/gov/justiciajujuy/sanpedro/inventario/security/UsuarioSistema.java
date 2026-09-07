package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.time.LocalDateTime;
import java.util.LinkedHashSet;
import java.util.Set;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.Table;

@Entity
@Table(name = "usuarios")
public class UsuarioSistema {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 120)
	private String username;

	@Column(name = "nombre_visible", nullable = false, length = 180)
	private String nombreVisible;

	@Column(nullable = false, length = 120)
	private String fuero;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 20)
	private OrigenIdentidad origen = OrigenIdentidad.AD;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	@ManyToMany
	@JoinTable(
			name = "usuario_roles",
			joinColumns = @JoinColumn(name = "usuario_id"),
			inverseJoinColumns = @JoinColumn(name = "rol_id"))
	private Set<Rol> roles = new LinkedHashSet<>();

	protected UsuarioSistema() {
	}

	public UsuarioSistema(String username, String nombreVisible, String fuero) {
		this(username, nombreVisible, fuero, OrigenIdentidad.AD);
	}

	public UsuarioSistema(String username, String nombreVisible, String fuero, OrigenIdentidad origen) {
		this.username = username;
		this.nombreVisible = nombreVisible;
		this.fuero = fuero;
		this.origen = origen;
	}

	public Long getId() {
		return id;
	}

	public String getUsername() {
		return username;
	}

	public String getNombreVisible() {
		return nombreVisible;
	}

	public String getFuero() {
		return fuero;
	}

	public OrigenIdentidad getOrigen() {
		return origen;
	}

	public boolean isActivo() {
		return activo;
	}

	public Set<Rol> getRoles() {
		return roles;
	}

	public void setActivo(boolean activo) {
		this.activo = activo;
	}

	public void agregarRol(Rol rol) {
		roles.add(rol);
	}

	public void reemplazarRoles(Set<Rol> roles) {
		this.roles.clear();
		this.roles.addAll(roles);
	}
}
