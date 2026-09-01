package ar.gov.justiciajujuy.sanpedro.inventario.actas;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ActaRepository extends JpaRepository<Acta, Long> {

	Optional<Acta> findByNumeroIgnoreCase(String numero);

	List<Acta> findTop20ByNumeroStartingWithOrderByNumeroDesc(String prefijo);

	@Query("""
			SELECT a
			FROM Acta a
			LEFT JOIN FETCH a.equipo e
			WHERE (:estado IS NULL OR a.estado = :estado)
			  AND (:tipo IS NULL OR a.tipo = :tipo)
			  AND (:query IS NULL
			    OR LOWER(a.numero) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(a.destinatario) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(a.responsableEntrega, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(a.responsableRecepcion, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(e.nombre, '')) LIKE LOWER(CONCAT('%', :query, '%')))
			ORDER BY a.fechaEmision DESC, a.numero
			""")
	List<Acta> buscar(@Param("query") String query, @Param("tipo") TipoActa tipo,
			@Param("estado") EstadoActa estado);
}
