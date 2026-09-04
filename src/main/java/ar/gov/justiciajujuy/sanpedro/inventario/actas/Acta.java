package ar.gov.justiciajujuy.sanpedro.inventario.actas;

import java.time.LocalDate;
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
@Table(name = "actas")
public class Acta {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 80)
	private String numero;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private TipoActa tipo = TipoActa.ENTREGA;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "equipo_id")
	private Equipo equipo;

	@Column(name = "fecha_emision")
	private LocalDate fechaEmision;

	@Column(nullable = false, length = 180)
	private String destinatario;

	@Column(name = "responsable_entrega", length = 120)
	private String responsableEntrega;

	@Column(name = "responsable_recepcion", length = 120)
	private String responsableRecepcion;

	@Column(nullable = false, length = 1000)
	private String detalle;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private EstadoActa estado = EstadoActa.BORRADOR;

	@Column(length = 500)
	private String observaciones;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected Acta() {
	}

	public Acta(String numero, TipoActa tipo, String destinatario, String detalle) {
		this.numero = numero;
		this.tipo = tipo;
		this.destinatario = destinatario;
		this.detalle = detalle;
	}

	public void actualizar(String numero, TipoActa tipo, Equipo equipo, LocalDate fechaEmision, String destinatario,
			String responsableEntrega, String responsableRecepcion, String detalle, EstadoActa estado,
			String observaciones, boolean activo) {
		this.numero = numero;
		this.tipo = tipo;
		this.equipo = equipo;
		this.fechaEmision = fechaEmision;
		this.destinatario = destinatario;
		this.responsableEntrega = responsableEntrega;
		this.responsableRecepcion = responsableRecepcion;
		this.detalle = detalle;
		this.estado = estado;
		this.observaciones = observaciones;
		this.activo = activo;
	}

	public Long getId() { return id; }
	public String getNumero() { return numero; }
	public TipoActa getTipo() { return tipo; }
	public Equipo getEquipo() { return equipo; }
	public LocalDate getFechaEmision() { return fechaEmision; }
	public String getDestinatario() { return destinatario; }
	public String getResponsableEntrega() { return responsableEntrega; }
	public String getResponsableRecepcion() { return responsableRecepcion; }
	public String getDetalle() { return detalle; }
	public EstadoActa getEstado() { return estado; }
	public String getObservaciones() { return observaciones; }
	public boolean isActivo() { return activo; }
	public void desvincularEquipo() { this.equipo = null; }
}
