package ar.gov.justiciajujuy.sanpedro.inventario.componentes;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ComponenteRepository extends JpaRepository<Componente, Long> {

	List<Componente> findByEquipoIdOrderByTipoAscDescripcionAsc(Long equipoId);

	List<Componente> findByEquipoIdAndOrigenOrderByTipoAscDescripcionAsc(Long equipoId, OrigenComponente origen);

	void deleteByEquipoIdAndOrigen(Long equipoId, OrigenComponente origen);

	void deleteByEquipoId(Long equipoId);
}
