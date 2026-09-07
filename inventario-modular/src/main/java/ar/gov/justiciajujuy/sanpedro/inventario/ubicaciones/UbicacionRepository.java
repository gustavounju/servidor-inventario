package ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface UbicacionRepository extends JpaRepository<Ubicacion, Long> {

	Optional<Ubicacion> findByCodigoIgnoreCase(String codigo);

	@Query("""
			SELECT u
			FROM Ubicacion u
			WHERE (:estado IS NULL OR u.estado = :estado)
			  AND (:tipo IS NULL OR u.tipo = :tipo)
			  AND (:query IS NULL
			    OR LOWER(u.codigo) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(u.nombre) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(u.fuero, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(u.responsable, '')) LIKE LOWER(CONCAT('%', :query, '%'))
			    OR LOWER(COALESCE(u.edificio, '')) LIKE LOWER(CONCAT('%', :query, '%')))
			ORDER BY u.nombre
			""")
	List<Ubicacion> buscar(@Param("query") String query, @Param("tipo") TipoUbicacion tipo,
			@Param("estado") EstadoUbicacion estado);
}
