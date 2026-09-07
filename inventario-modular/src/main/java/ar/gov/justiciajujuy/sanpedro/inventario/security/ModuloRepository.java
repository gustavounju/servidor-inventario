package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ModuloRepository extends JpaRepository<Modulo, Long> {

	@Query(value = """
			SELECT
			  m.codigo AS moduloCodigo,
			  m.nombre AS moduloNombre,
			  m.descripcion AS moduloDescripcion,
			  m.orden AS moduloOrden,
			  p.codigo AS permisoCodigo
			FROM usuarios u
			JOIN usuario_roles ur ON ur.usuario_id = u.id
			JOIN roles r ON r.id = ur.rol_id
			JOIN rol_modulo_permisos rmp ON rmp.rol_id = r.id
			JOIN modulos m ON m.id = rmp.modulo_id
			JOIN permisos p ON p.id = rmp.permiso_id
			WHERE LOWER(u.username) = LOWER(:username)
			  AND u.activo = TRUE
			  AND r.activo = TRUE
			  AND m.activo = TRUE
			ORDER BY m.orden, p.codigo
			""", nativeQuery = true)
	List<ModuloPermisoProjection> findAllowedModulesByUsername(@Param("username") String username);
}
