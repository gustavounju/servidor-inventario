package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CredencialLocalRepository extends JpaRepository<CredencialLocal, Long> {

	boolean existsByUsuarioUsernameIgnoreCase(String username);

	@Query("""
			SELECT c
			FROM CredencialLocal c
			JOIN FETCH c.usuario u
			WHERE LOWER(u.username) = LOWER(:username)
			  AND u.activo = true
			  AND u.origen = ar.gov.justiciajujuy.sanpedro.inventario.security.OrigenIdentidad.LOCAL
			""")
	Optional<CredencialLocal> findActivaByUsername(@Param("username") String username);
}
