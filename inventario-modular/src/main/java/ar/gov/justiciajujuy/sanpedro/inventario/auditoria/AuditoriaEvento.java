package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "auditoria_eventos")
public class AuditoriaEvento {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(name = "usuario", nullable = false, length = 120)
	private String usuario;

	@Column(name = "modulo", nullable = false, length = 60)
	private String modulo;

	@Column(name = "accion", nullable = false, length = 80)
	private String accion;

	@Column(name = "entidad_tipo", nullable = false, length = 80)
	private String entidadTipo;

	@Column(name = "entidad_id")
	private Long entidadId;

	@Column(name = "detalle", nullable = false, length = 1000)
	private String detalle;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	protected AuditoriaEvento() {
	}

	public AuditoriaEvento(String usuario, String modulo, String accion, String entidadTipo, Long entidadId, String detalle) {
		this.usuario = usuario;
		this.modulo = modulo;
		this.accion = accion;
		this.entidadTipo = entidadTipo;
		this.entidadId = entidadId;
		this.detalle = detalle;
	}

	public Long getId() {
		return id;
	}

	public String getUsuario() {
		return usuario;
	}

	public String getModulo() {
		return modulo;
	}

	public String getAccion() {
		return accion;
	}

	public String getEntidadTipo() {
		return entidadTipo;
	}

	public Long getEntidadId() {
		return entidadId;
	}

	public String getDetalle() {
		return detalle;
	}

	public LocalDateTime getCreadoEn() {
		return creadoEn;
	}
}
