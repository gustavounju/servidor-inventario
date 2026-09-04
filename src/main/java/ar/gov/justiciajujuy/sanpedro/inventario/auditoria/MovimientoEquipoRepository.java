package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MovimientoEquipoRepository extends JpaRepository<MovimientoEquipo, Long> {
    List<MovimientoEquipo> findByEquipoIdOrderByFechaMovimientoDesc(Long equipoId);
    void deleteByEquipoId(Long equipoId);
}
