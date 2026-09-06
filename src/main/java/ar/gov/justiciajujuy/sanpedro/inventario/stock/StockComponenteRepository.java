package ar.gov.justiciajujuy.sanpedro.inventario.stock;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface StockComponenteRepository extends JpaRepository<StockComponente, Long> {

	List<StockComponente> findByActivoTrueOrderByTipoAscDescripcionAsc();

	/** Busca piezas activas en stock que coincidan con un número de serie específico. */
	List<StockComponente> findBySerialAndActivoTrue(String serial);
}
