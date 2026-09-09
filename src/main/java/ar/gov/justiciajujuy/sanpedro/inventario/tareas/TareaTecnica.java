package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.time.LocalDateTime;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "tareas_tecnicas")
public class TareaTecnica {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "equipo_id")
	private Equipo equipo;

	@Column(nullable = false, length = 180)
	private String titulo;

	@Column(length = 1000)
	private String descripcion;

	@Column(name = "solicitante_username", length = 120)
	private String solicitanteUsername;

	@Column(name = "solicitante_nombre", length = 180)
	private String solicitanteNombre;

	@Column(name = "solicitante_fuero", length = 120)
	private String solicitanteFuero;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private EstadoTareaTecnica estado = EstadoTareaTecnica.PENDIENTE;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private PrioridadTareaTecnica prioridad = PrioridadTareaTecnica.MEDIA;

	@Column(length = 120)
	private String responsable;

	@Column(name = "creado_por", length = 120)
	private String creadoPor;

	@Column(name = "observaciones_cierre", length = 1000)
	private String observacionesCierre;

	@Column(name = "cerrado_en")
	private LocalDateTime cerradoEn;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected TareaTecnica() {
	}

	public TareaTecnica(String titulo) {
		this.titulo = titulo;
	}

	public void actualizarDatos(Equipo equipo, String titulo, String descripcion,
			String solicitanteUsername, String solicitanteNombre, String solicitanteFuero,
			PrioridadTareaTecnica prioridad, String responsable) {
		this.equipo = equipo;
		this.titulo = titulo;
		this.descripcion = descripcion;
		this.solicitanteUsername = solicitanteUsername;
		this.solicitanteNombre = solicitanteNombre;
		this.solicitanteFuero = solicitanteFuero;
		this.prioridad = prioridad;
		this.responsable = responsable;
	}

	public void marcarCreadoPor(String creadoPor) {
		if (this.creadoPor == null) {
			this.creadoPor = creadoPor;
		}
	}

	public void tomar(String responsable) {
		this.responsable = responsable;
		this.estado = EstadoTareaTecnica.EN_PROCESO;
	}

	public void reasignarEquipo(Equipo equipo) {
		this.equipo = equipo;
	}

	public void cambiarEstado(EstadoTareaTecnica estado, String observacionesCierre) {
		this.estado = estado;
		this.observacionesCierre = observacionesCierre;
		this.cerradoEn = estado == EstadoTareaTecnica.CERRADA || estado == EstadoTareaTecnica.CANCELADA
				? LocalDateTime.now()
				: null;
	}

	public Long getId() { return id; }
	public Equipo getEquipo() { return equipo; }
	public String getTitulo() { return titulo; }
	public String getDescripcion() { return descripcion; }
	public EstadoTareaTecnica getEstado() { return estado; }
	public PrioridadTareaTecnica getPrioridad() { return prioridad; }
	public String getSolicitanteUsername() { return solicitanteUsername; }
	public String getSolicitanteNombre() { return solicitanteNombre; }
	public String getSolicitanteFuero() { return solicitanteFuero; }
	public String getResponsable() { return responsable; }
	public String getCreadoPor() { return creadoPor; }
	public String getObservacionesCierre() { return observacionesCierre; }
	public void desvincularEquipo() { this.equipo = null; }
	public LocalDateTime getCerradoEn() { return cerradoEn; }
	public LocalDateTime getCreadoEn() { return creadoEn; }
}
