package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "credenciales_locales")
public class CredencialLocal {

	@Id
	@Column(name = "usuario_id")
	private Long usuarioId;

	@OneToOne(fetch = FetchType.LAZY)
	@MapsId
	@JoinColumn(name = "usuario_id")
	private UsuarioSistema usuario;

	@Column(name = "password_hash", nullable = false, length = 255)
	private String passwordHash;

	@Column(name = "requiere_cambio_clave", nullable = false)
	private boolean requiereCambioClave;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected CredencialLocal() {
	}

	public CredencialLocal(UsuarioSistema usuario, String passwordHash, boolean requiereCambioClave) {
		this.usuario = usuario;
		this.passwordHash = passwordHash;
		this.requiereCambioClave = requiereCambioClave;
	}

	public UsuarioSistema getUsuario() {
		return usuario;
	}

	public String getPasswordHash() {
		return passwordHash;
	}

	public void setPasswordHash(String passwordHash) {
		this.passwordHash = passwordHash;
	}

	public boolean isRequiereCambioClave() {
		return requiereCambioClave;
	}
}
