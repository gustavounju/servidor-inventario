package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Optional;
import java.util.Set;

import org.springframework.data.jpa.repository.JpaRepository;

public interface RolRepository extends JpaRepository<Rol, Long> {

	Optional<Rol> findByCodigo(String codigo);

	Set<Rol> findByCodigoInAndActivoTrue(Set<String> codigos);
}
