package ar.gov.justiciajujuy.sanpedro.inventario.tareas;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface TareaTecnicaRepository extends JpaRepository<TareaTecnica, Long> {

	// Leer y asignar bajo el mismo bloqueo: dos celulares no pueden ganar la toma simultaneamente.
	@org.springframework.data.jpa.repository.Lock(jakarta.persistence.LockModeType.PESSIMISTIC_WRITE)
	@Query("SELECT t FROM TareaTecnica t WHERE t.id = :id")
	java.util.Optional<TareaTecnica> buscarParaTomar(@Param("id") Long id);

	@Query("""
			SELECT t
			FROM TareaTecnica t
			LEFT JOIN FETCH t.equipo e
			WHERE (:estado IS NULL OR t.estado = :estado)
			  AND (:equipoId IS NULL OR e.id = :equipoId)
			  AND (:responsable IS NULL
			    OR LOWER(t.titulo) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.descripcion, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.solicitanteUsername, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.solicitanteNombre, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.solicitanteFuero, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(t.responsable, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR LOWER(COALESCE(e.nombre, '')) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    OR EXISTS (
			      SELECT 1
			      FROM TareaTecnicaComentario c
			      WHERE c.tarea = t
			        AND LOWER(c.comentario) LIKE LOWER(CONCAT('%', :responsable, '%'))
			    ))
			ORDER BY t.id DESC
			""")
	List<TareaTecnica> buscar(
			@Param("estado") EstadoTareaTecnica estado,
			@Param("equipoId") Long equipoId,
			@Param("responsable") String responsable);

	long countByEstado(EstadoTareaTecnica estado);

	long countByCreadoEnBetween(java.time.LocalDateTime desde, java.time.LocalDateTime hasta);

	long countByCerradoEnBetween(java.time.LocalDateTime desde, java.time.LocalDateTime hasta);

	List<TareaTecnica> findByEquipoId(Long equipoId);
}
