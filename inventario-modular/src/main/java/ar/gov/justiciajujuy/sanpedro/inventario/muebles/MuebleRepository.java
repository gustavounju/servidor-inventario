package ar.gov.justiciajujuy.sanpedro.inventario.muebles;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface MuebleRepository extends JpaRepository<Mueble, Long> {

	Optional<Mueble> findByCodigoIgnoreCase(String codigo);

	@Query("""
			SELECT m
			FROM Mueble m
			WHERE (:estado IS NULL OR m.estado = :estado)
			  AND (:query IS NULL
			    OR LOWER(m.codigo) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(m.tipo) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(m.descripcion) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(m.ubicacion, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(m.fuero, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(m.responsable, '')) LIKE LOWER(CONCAT('%', :query, '%')))
			ORDER BY m.codigo
			""")
	List<Mueble> buscar(@Param("query") String query, @Param("estado") EstadoMueble estado);
}
