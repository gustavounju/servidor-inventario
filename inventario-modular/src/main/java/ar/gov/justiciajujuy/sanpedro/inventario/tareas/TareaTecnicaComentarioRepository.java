package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface TareaTecnicaComentarioRepository extends JpaRepository<TareaTecnicaComentario, Long> {

	List<TareaTecnicaComentario> findByTareaIdOrderByCreadoEnDescIdDesc(Long tareaId);
 
 	void deleteByTareaId(Long tareaId);
}
