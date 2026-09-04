package ar.gov.justiciajujuy.sanpedro.inventario.patrimonio;

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
@Table(name = "bienes_patrimoniales")
public class BienPatrimonial {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(name = "numero_patrimonial", nullable = false, unique = true, length = 80)
	private String numeroPatrimonial;

	@Column(nullable = false, length = 80)
	private String categoria;

	@Column(nullable = false, length = 255)
	private String descripcion;

	@Column(length = 180)
	private String ubicacion;

	@Column(length = 120)
	private String fuero;

	@Column(length = 120)
	private String custodio;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private EstadoBienPatrimonial estado = EstadoBienPatrimonial.EN_USO;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "equipo_id")
	private Equipo equipo;

	@Column(length = 500)
	private String observaciones;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected BienPatrimonial() {
	}

	public BienPatrimonial(String numeroPatrimonial, String categoria, String descripcion) {
		this.numeroPatrimonial = numeroPatrimonial;
		this.categoria = categoria;
		this.descripcion = descripcion;
	}

	public void actualizar(String numeroPatrimonial, String categoria, String descripcion, String ubicacion,
			String fuero, String custodio, EstadoBienPatrimonial estado, Equipo equipo, String observaciones,
			boolean activo) {
		this.numeroPatrimonial = numeroPatrimonial;
		this.categoria = categoria;
		this.descripcion = descripcion;
		this.ubicacion = ubicacion;
		this.fuero = fuero;
		this.custodio = custodio;
		this.estado = estado;
		this.equipo = equipo;
		this.observaciones = observaciones;
		this.activo = activo;
	}

	public Long getId() { return id; }
	public String getNumeroPatrimonial() { return numeroPatrimonial; }
	public String getCategoria() { return categoria; }
	public String getDescripcion() { return descripcion; }
	public String getUbicacion() { return ubicacion; }
	public String getFuero() { return fuero; }
	public String getCustodio() { return custodio; }
	public EstadoBienPatrimonial getEstado() { return estado; }
	public Equipo getEquipo() { return equipo; }
	public String getObservaciones() { return observaciones; }
	public boolean isActivo() { return activo; }
	public void desvincularEquipo() { this.equipo = null; }
}
