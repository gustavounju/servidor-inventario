package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface UsuarioSistemaRepository extends JpaRepository<UsuarioSistema, Long> {

	Optional<UsuarioSistema> findByUsernameIgnoreCase(String username);

	boolean existsByUsernameIgnoreCase(String username);

	@Query("""
			SELECT DISTINCT u
			FROM UsuarioSistema u
			LEFT JOIN FETCH u.roles
			ORDER BY u.username
			""")
	java.util.List<UsuarioSistema> findAllWithRoles();
}
