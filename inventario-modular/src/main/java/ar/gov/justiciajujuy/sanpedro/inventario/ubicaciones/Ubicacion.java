package ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones;

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
@Table(name = "ubicaciones")
public class Ubicacion {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 80)
	private String codigo;

	@Column(nullable = false, length = 180)
	private String nombre;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private TipoUbicacion tipo = TipoUbicacion.OFICINA;

	@Column(length = 120)
	private String fuero;

	@Column(length = 120)
	private String responsable;

	@Column(length = 120)
	private String edificio;

	@Column(length = 40)
	private String piso;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 40)
	private EstadoUbicacion estado = EstadoUbicacion.ACTIVA;

	@Column(length = 500)
	private String observaciones;

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected Ubicacion() {
	}

	public Ubicacion(String codigo, String nombre, TipoUbicacion tipo) {
		this.codigo = codigo;
		this.nombre = nombre;
		this.tipo = tipo;
	}

	public void actualizar(String codigo, String nombre, TipoUbicacion tipo, String fuero, String responsable,
			String edificio, String piso, EstadoUbicacion estado, String observaciones, boolean activo) {
		this.codigo = codigo;
		this.nombre = nombre;
		this.tipo = tipo;
		this.fuero = fuero;
		this.responsable = responsable;
		this.edificio = edificio;
		this.piso = piso;
		this.estado = estado;
		this.observaciones = observaciones;
		this.activo = activo;
	}

	public Long getId() { return id; }
	public String getCodigo() { return codigo; }
	public String getNombre() { return nombre; }
	public TipoUbicacion getTipo() { return tipo; }
	public String getFuero() { return fuero; }
	public String getResponsable() { return responsable; }
	public String getEdificio() { return edificio; }
	public String getPiso() { return piso; }
	public EstadoUbicacion getEstado() { return estado; }
	public String getObservaciones() { return observaciones; }
	public boolean isActivo() { return activo; }
}
