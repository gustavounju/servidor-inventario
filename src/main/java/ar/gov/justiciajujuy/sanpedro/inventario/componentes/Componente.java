package ar.gov.justiciajujuy.sanpedro.inventario.componentes;

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
@Table(name = "componentes")
public class Componente {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "equipo_id", nullable = false)
	private Equipo equipo;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 60)
	private TipoComponente tipo;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private OrigenComponente origen;

	@Enumerated(EnumType.STRING)
	@Column(name = "estado_comparacion", nullable = false, length = 40)
	private EstadoComparacion estadoComparacion;

	@Column(nullable = false, length = 255)
	private String descripcion;

	@Column(length = 120)
	private String marca;

	@Column(length = 180)
	private String modelo;

	@Column(length = 180)
	private String serial;

	@Column(length = 120)
	private String capacidad;

	@Column(length = 80)
	private String remito;

	@Column(name = "orden_compra", length = 80)
	private String ordenCompra;

	@Column(length = 120)
	private String proveedor;

	@Column(length = 120)
	private String ubicacion;

	@Column(length = 500)
	private String observaciones;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected Componente() {
	}

	public Componente(Equipo equipo, TipoComponente tipo, OrigenComponente origen, EstadoComparacion estadoComparacion, String descripcion) {
		this.equipo = equipo;
		this.tipo = tipo;
		this.origen = origen;
		this.estadoComparacion = estadoComparacion;
		this.descripcion = descripcion;
	}

	public Long getId() {
		return id;
	}

	public Equipo getEquipo() {
		return equipo;
	}

	public TipoComponente getTipo() {
		return tipo;
	}

	public OrigenComponente getOrigen() {
		return origen;
	}

	public EstadoComparacion getEstadoComparacion() {
		return estadoComparacion;
	}

	public String getDescripcion() {
		return descripcion;
	}

	public String getMarca() {
		return marca;
	}

	public String getModelo() {
		return modelo;
	}

	public String getSerial() {
		return serial;
	}

	public String getCapacidad() {
		return capacidad;
	}

	public String getRemito() {
		return remito;
	}

	public String getOrdenCompra() {
		return ordenCompra;
	}

	public String getProveedor() {
		return proveedor;
	}

	public String getUbicacion() {
		return ubicacion;
	}

	public String getObservaciones() {
		return observaciones;
	}

	public boolean isActivo() {
		return activo;
	}

	public void actualizar(TipoComponente tipo, OrigenComponente origen, EstadoComparacion estadoComparacion, String descripcion,
			String marca, String modelo, String serial, String capacidad, String remito, String ordenCompra, String proveedor,
			String ubicacion, String observaciones, boolean activo) {
		this.tipo = tipo;
		this.origen = origen;
		this.estadoComparacion = estadoComparacion;
		this.descripcion = descripcion;
		this.marca = marca;
		this.modelo = modelo;
		this.serial = serial;
		this.capacidad = capacidad;
		this.remito = remito;
		this.ordenCompra = ordenCompra;
		this.proveedor = proveedor;
		this.ubicacion = ubicacion;
		this.observaciones = observaciones;
		this.activo = activo;
	}
}
