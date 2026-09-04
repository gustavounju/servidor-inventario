package ar.gov.justiciajujuy.sanpedro.inventario.armado;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface OrdenArmadoComponenteRepository extends JpaRepository<OrdenArmadoComponente, Long> {

	List<OrdenArmadoComponente> findByOrdenEquipoIdOrderByIdAsc(Long equipoId);
 
 	List<OrdenArmadoComponente> findByOrdenId(Long ordenId);
 
 	void deleteByOrdenId(Long ordenId);
}
