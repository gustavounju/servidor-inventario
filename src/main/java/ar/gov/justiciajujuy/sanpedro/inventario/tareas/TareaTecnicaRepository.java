package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface TareaTecnicaRepository extends JpaRepository<TareaTecnica, Long> {

	@Query("""
			SELECT t
			FROM TareaTecnica t
			LEFT JOIN FETCH t.equipo e
			WHERE (:estado IS NULL OR t.estado = :estado)
			  AND (:equipoId IS NULL OR e.id = :equipoId)
			  AND (:responsable IS NULL
			    OR LOWER(t.titulo) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.descripcion, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.responsable, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(e.nombre, '')) LIKE LOWER(CONCAT('%', :responsable, '%')))
			ORDER BY t.id DESC
			""")
	List<TareaTecnica> buscar(
			@Param("estado") EstadoTareaTecnica estado,
			@Param("equipoId") Long equipoId,
			@Param("responsable") String responsable);
}
