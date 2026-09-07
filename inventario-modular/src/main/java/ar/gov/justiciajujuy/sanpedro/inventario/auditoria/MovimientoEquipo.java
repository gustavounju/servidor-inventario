package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import java.time.LocalDateTime;
import jakarta.persistence.*;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;

@Entity
@Table(name = "movimientos_equipo")
public class MovimientoEquipo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "equipo_id", nullable = false)
    private Equipo equipo;

    @Enumerated(EnumType.STRING)
    @Column(name = "tipo_movimiento", nullable = false, length = 60)
    private TipoMovimiento tipoMovimiento;

    @Column(name = "usuario_destino", length = 120)
    private String usuarioDestino;

    @Column(name = "ubicacion_origen", length = 120)
    private String ubicacionOrigen;

    @Column(name = "ubicacion_destino", length = 120)
    private String ubicacionDestino;

    @Column(name = "registrado_por", nullable = false, length = 120)
    private String registradoPor;

    @Column(length = 500)
    private String observaciones;

    @Column(name = "fecha_movimiento", nullable = false)
    private LocalDateTime fechaMovimiento;

    protected MovimientoEquipo() {}

    public MovimientoEquipo(Equipo equipo, TipoMovimiento tipoMovimiento, String usuarioDestino, String ubicacionOrigen, String ubicacionDestino, String registradoPor, String observaciones) {
        this.equipo = equipo;
        this.tipoMovimiento = tipoMovimiento;
        this.usuarioDestino = usuarioDestino;
        this.ubicacionOrigen = ubicacionOrigen;
        this.ubicacionDestino = ubicacionDestino;
        this.registradoPor = registradoPor;
        this.observaciones = observaciones;
        this.fechaMovimiento = LocalDateTime.now();
    }

    // Getters
    public Long getId() { return id; }
    public Equipo getEquipo() { return equipo; }
    public TipoMovimiento getTipoMovimiento() { return tipoMovimiento; }
    public String getUsuarioDestino() { return usuarioDestino; }
    public String getUbicacionOrigen() { return ubicacionOrigen; }
    public String getUbicacionDestino() { return ubicacionDestino; }
    public String getRegistradoPor() { return registradoPor; }
    public String getObservaciones() { return observaciones; }
    public LocalDateTime getFechaMovimiento() { return fechaMovimiento; }
}
