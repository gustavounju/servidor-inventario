package ar.gov.justiciajujuy.sanpedro.inventario.equipos;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "equipos")
public class Equipo {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, unique = true, length = 120)
	private String nombre;

	@Column(name = "ultimo_usuario", length = 120)
	private String ultimoUsuario;

	@Column(nullable = false, length = 120)
	private String fuero;

	@Column(length = 180)
	private String ubicacion;

	@Column(length = 45)
	private String ip;

	@Column(name = "sistema_operativo", length = 180)
	private String sistemaOperativo;

	@Column(length = 255)
	private String procesador;

	@Column(name = "ram_mb")
	private Integer ramMb;

	@Column(name = "ram_detalles", length = 500)
	private String ramDetalles;

	@Column(name = "ram_seriales", length = 500)
	private String ramSeriales;

	@Column(name = "discos_modelos", length = 500)
	private String discosModelos;

	@Column(name = "discos_seriales", length = 500)
	private String discosSeriales;

	@Column(name = "motherboard_modelo", length = 255)
	private String motherboardModelo;

	@Column(name = "motherboard_serial", length = 255)
	private String motherboardSerial;

	@Column(length = 500)
	private String monitores;

	@Column(length = 180)
	private String teclado;

	@Column(length = 180)
	private String mouse;

	@Column(length = 180)
	private String impresora;

	@Column(nullable = false, length = 60)
	private String monitoreo = "SIN_REPORTE";

	@Column(nullable = false)
	private boolean activo = true;

	@Column(name = "ultimo_reporte_en")
	private LocalDateTime ultimoReporteEn;

	@Column(name = "creado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime creadoEn;

	@Column(name = "actualizado_en", nullable = false, insertable = false, updatable = false)
	private LocalDateTime actualizadoEn;

	protected Equipo() {
	}

	public Equipo(String nombre, String fuero) {
		this.nombre = nombre;
		this.fuero = fuero;
	}

	public static Equipo crearParaTaller(String nombre) {
		Equipo equipo = new Equipo(nombre, "Taller de Informática");
		equipo.ubicacion = "Taller de Informática";
		equipo.ultimoUsuario = "Sin asignar";
		equipo.sistemaOperativo = "Pendiente de instalación / relevamiento";
		equipo.activo = true;
		return equipo;
	}

	public Long getId() {
		return id;
	}

	public String getNombre() {
		return nombre;
	}

	public String getUltimoUsuario() {
		return ultimoUsuario;
	}

	public String getFuero() {
		return fuero;
	}

	public String getUbicacion() {
		return ubicacion;
	}

	public String getIp() {
		return ip;
	}

	public String getSistemaOperativo() {
		return sistemaOperativo;
	}

	public String getProcesador() {
		return procesador;
	}

	public Integer getRamMb() {
		return ramMb;
	}

	public String getRamDetalles() {
		return ramDetalles;
	}

	public String getRamSeriales() {
		return ramSeriales;
	}

	public String getDiscosModelos() {
		return discosModelos;
	}

	public String getDiscosSeriales() {
		return discosSeriales;
	}

	public String getMotherboardModelo() {
		return motherboardModelo;
	}

	public String getMotherboardSerial() {
		return motherboardSerial;
	}

	public String getMonitores() {
		return monitores;
	}

	public String getTeclado() {
		return teclado;
	}

	public String getMouse() {
		return mouse;
	}

	public String getImpresora() {
		return impresora;
	}

	public String getMonitoreo() {
		return monitoreo;
	}

	public boolean isActivo() {
		return activo;
	}

	public LocalDateTime getUltimoReporteEn() {
		return ultimoReporteEn;
	}

	public void actualizarDesdeReporte(
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String procesador,
			Integer ramMb,
			String ramDetalles,
			String ramSeriales,
			String discosModelos,
			String discosSeriales,
			String motherboardModelo,
			String motherboardSerial,
			String monitores,
			String teclado,
			String mouse,
			String impresora,
			boolean activo,
			LocalDateTime reportadoEn) {
		this.ultimoUsuario = ultimoUsuario;
		this.fuero = fuero;
		this.ubicacion = ubicacion;
		this.ip = ip;
		this.sistemaOperativo = sistemaOperativo;
		this.procesador = procesador;
		this.ramMb = ramMb;
		this.ramDetalles = ramDetalles;
		this.ramSeriales = ramSeriales;
		this.discosModelos = discosModelos;
		this.discosSeriales = discosSeriales;
		this.motherboardModelo = motherboardModelo;
		this.motherboardSerial = motherboardSerial;
		this.monitores = monitores;
		this.teclado = teclado;
		this.mouse = mouse;
		this.impresora = impresora;
		this.activo = activo;
		this.monitoreo = "REPORTADO";
		this.ultimoReporteEn = reportadoEn;
	}

	public void actualizarManualmente(
			String nombre,
			String ultimoUsuario,
			String fuero,
			String ubicacion,
			String ip,
			String sistemaOperativo,
			String procesador,
			Integer ramMb,
			String ramDetalles,
			String ramSeriales,
			String discosModelos,
			String discosSeriales,
			String motherboardModelo,
			String motherboardSerial,
			String monitores,
			String teclado,
			String mouse,
			String impresora,
			boolean activo) {
		this.nombre = nombre;
		this.ultimoUsuario = ultimoUsuario;
		this.fuero = fuero;
		this.ubicacion = ubicacion;
		this.ip = ip;
		this.sistemaOperativo = sistemaOperativo;
		this.procesador = procesador;
		this.ramMb = ramMb;
		this.ramDetalles = ramDetalles;
		this.ramSeriales = ramSeriales;
		this.discosModelos = discosModelos;
		this.discosSeriales = discosSeriales;
		this.motherboardModelo = motherboardModelo;
		this.motherboardSerial = motherboardSerial;
		this.monitores = monitores;
		this.teclado = teclado;
		this.mouse = mouse;
		this.impresora = impresora;
		this.activo = activo;
	}
}
