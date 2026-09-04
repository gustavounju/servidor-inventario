package ar.gov.justiciajujuy.sanpedro.inventario.patrimonio;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface BienPatrimonialRepository extends JpaRepository<BienPatrimonial, Long> {

	Optional<BienPatrimonial> findByNumeroPatrimonialIgnoreCase(String numeroPatrimonial);

	@Query("""
			SELECT b
			FROM BienPatrimonial b
			LEFT JOIN FETCH b.equipo e
			WHERE (:estado IS NULL OR b.estado = :estado)
			  AND (:query IS NULL
			    OR LOWER(b.numeroPatrimonial) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(b.categoria) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(b.descripcion) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(b.ubicacion, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(b.fuero, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(b.custodio, '')) LIKE LOWER(CONCAT('%', :query, '%')))
			ORDER BY b.numeroPatrimonial
			""")
	List<BienPatrimonial> buscar(@Param("query") String query, @Param("estado") EstadoBienPatrimonial estado);

	List<BienPatrimonial> findByEquipoId(Long equipoId);
}
