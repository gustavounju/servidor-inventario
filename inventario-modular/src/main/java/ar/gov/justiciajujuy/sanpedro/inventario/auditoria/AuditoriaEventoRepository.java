package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface AuditoriaEventoRepository extends JpaRepository<AuditoriaEvento, Long> {

	List<AuditoriaEvento> findTop100ByOrderByIdDesc();

	@Query("""
			select e from AuditoriaEvento e
			where (:usuario is null or lower(e.usuario) like lower(concat('%', :usuario, '%')))
			  and (:modulo is null or lower(e.modulo) = lower(:modulo))
			  and (:accion is null or lower(e.accion) = lower(:accion))
			order by e.id desc
			limit 100
			""")
	List<AuditoriaEvento> filtrarRecientes(String usuario, String modulo, String accion);
}
