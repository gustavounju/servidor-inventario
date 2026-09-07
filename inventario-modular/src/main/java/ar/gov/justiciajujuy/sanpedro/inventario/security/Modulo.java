package ar.gov.justiciajujuy.sanpedro.inventario.security;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "modulos")
public class Modulo {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 60)
	private String codigo;

	@Column(nullable = false, length = 120)
	private String nombre;

	@Column(nullable = false, length = 255)
	private String descripcion;

	@Column(nullable = false)
	private int orden;

	@Column(nullable = false)
	private boolean activo = true;

	protected Modulo() {
	}

	public Modulo(String codigo, String nombre, String descripcion, int orden) {
		this.codigo = codigo;
		this.nombre = nombre;
		this.descripcion = descripcion;
		this.orden = orden;
	}

	public Long getId() {
		return id;
	}

	public String getCodigo() {
		return codigo;
	}

	public String getNombre() {
		return nombre;
	}

	public String getDescripcion() {
		return descripcion;
	}

	public int getOrden() {
		return orden;
	}

	public boolean isActivo() {
		return activo;
	}
}
