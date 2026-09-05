package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface MovimientoEquipoRepository extends JpaRepository<MovimientoEquipo, Long> {
    List<MovimientoEquipo> findByEquipoIdOrderByFechaMovimientoDesc(Long equipoId);

    @Query("""
			select m from MovimientoEquipo m
			where m.equipo.id = :equipoId
			  and (:usuario is null or lower(m.registradoPor) like lower(concat('%', :usuario, '%')) or lower(m.usuarioDestino) like lower(concat('%', :usuario, '%')))
			  and (:tipo is null or m.tipoMovimiento = :tipo)
			order by m.fechaMovimiento desc
			""")
    List<MovimientoEquipo> filtrarPorEquipo(Long equipoId, String usuario, TipoMovimiento tipo);

    void deleteByEquipoId(Long equipoId);
}
