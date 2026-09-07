package ar.gov.justiciajujuy.sanpedro.inventario.muebles;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "muebles")
public class Mueble {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 80)
	private String codigo;

	@Column(nullable = false, length = 80)
	private String tipo;

	@Column(nullable = false, length = 255)
	private String descripcion;

	@Column(length = 180)
	private String ubicacion;

	@Column(length = 120)
	private String fuero;

	@Column(length = 120)
	private String responsable;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private EstadoMueble estado = EstadoMueble.ACTIVO;

	@Column(length = 500)
	private String observaciones;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected Mueble() {
	}

	public Mueble(String codigo, String tipo, String descripcion) {
		this.codigo = codigo;
		this.tipo = tipo;
		this.descripcion = descripcion;
	}

	public void actualizar(String codigo, String tipo, String descripcion, String ubicacion, String fuero,
			String responsable, EstadoMueble estado, String observaciones, boolean activo) {
		this.codigo = codigo;
		this.tipo = tipo;
		this.descripcion = descripcion;
		this.ubicacion = ubicacion;
		this.fuero = fuero;
		this.responsable = responsable;
		this.estado = estado;
		this.observaciones = observaciones;
		this.activo = activo;
	}

	public Long getId() { return id; }
	public String getCodigo() { return codigo; }
	public String getTipo() { return tipo; }
	public String getDescripcion() { return descripcion; }
	public String getUbicacion() { return ubicacion; }
	public String getFuero() { return fuero; }
	public String getResponsable() { return responsable; }
	public EstadoMueble getEstado() { return estado; }
	public String getObservaciones() { return observaciones; }
	public boolean isActivo() { return activo; }
}
