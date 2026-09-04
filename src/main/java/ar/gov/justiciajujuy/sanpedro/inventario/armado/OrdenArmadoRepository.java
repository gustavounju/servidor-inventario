package ar.gov.justiciajujuy.sanpedro.inventario.armado;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface OrdenArmadoRepository extends JpaRepository<OrdenArmado, Long> {

	List<OrdenArmado> findAllByOrderByIdDesc();

	List<OrdenArmado> findByEquipoIdOrderByIdDesc(Long equipoId);
 
 	void deleteByEquipoId(Long equipoId);
}
