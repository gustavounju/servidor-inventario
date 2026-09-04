package ar.gov.justiciajujuy.sanpedro.inventario.stock;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class StockService {

	private final StockComponenteRepository stockComponenteRepository;
	private final AuditoriaService auditoriaService;

	public StockService(StockComponenteRepository stockComponenteRepository, AuditoriaService auditoriaService) {
		this.stockComponenteRepository = stockComponenteRepository;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<StockComponenteDetalle> listarDisponiblesYActivos() {
		return stockComponenteRepository.findByActivoTrueOrderByTipoAscDescripcionAsc().stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional
	public StockComponenteDetalle crear(GuardarStockComponenteCommand command) {
		StockComponente componente = new StockComponente(command.tipo(), textoRequerido(command.descripcion(), "descripcion"));
		aplicarCampos(componente, command);
		StockComponente guardado = stockComponenteRepository.save(componente);
		auditoriaService.registrar("STOCK", "CREAR", "StockComponente", guardado.getId(),
				"Componente de stock " + guardado.getTipo() + " creado con estado " + guardado.getEstado() + ".");
		return toDetalle(guardado);
	}

	@Transactional
	public StockComponenteDetalle actualizar(Long id, GuardarStockComponenteCommand command) {
		StockComponente componente = stockComponenteRepository.findById(id)
				.orElseThrow(() -> new StockComponenteNoEncontradoException(id));
		aplicarCampos(componente, command);
		StockComponente guardado = stockComponenteRepository.save(componente);
		auditoriaService.registrar("STOCK", "ACTUALIZAR", "StockComponente", guardado.getId(),
				"Componente de stock " + guardado.getTipo() + " actualizado con estado " + guardado.getEstado() + ".");
		return toDetalle(guardado);
	}

	@Transactional
	public StockComponente reservar(Long id) {
		StockComponente componente = stockComponenteRepository.findById(id)
				.orElseThrow(() -> new StockComponenteNoEncontradoException(id));
		if (componente.getEstado() != EstadoStockComponente.DISPONIBLE) {
			throw new StockComponenteNoDisponibleException(id);
		}
		componente.reservar();
		auditoriaService.registrar("STOCK", "RESERVAR", "StockComponente", componente.getId(),
				"Componente de stock reservado: " + componente.getDescripcion() + ".");
		return componente;
	}

	@Transactional
	public StockComponente asignarReservado(Long id) {
		StockComponente componente = stockComponenteRepository.findById(id)
				.orElseThrow(() -> new StockComponenteNoEncontradoException(id));
		if (componente.getEstado() == EstadoStockComponente.ASIGNADO) {
			return componente;
		}
		if (componente.getEstado() != EstadoStockComponente.RESERVADO) {
			throw new StockComponenteNoReservadoException(id);
		}
		componente.asignar();
		auditoriaService.registrar("STOCK", "ASIGNAR", "StockComponente", componente.getId(),
				"Salida real confirmada para stock: " + componente.getDescripcion() + ".");
		return componente;
	}

	private void aplicarCampos(StockComponente componente, GuardarStockComponenteCommand command) {
		componente.actualizar(
				command.tipo(),
				command.estado(),
				textoRequerido(command.descripcion(), "descripcion"),
				textoOpcional(command.marca()),
				textoOpcional(command.modelo()),
				textoOpcional(command.serial()),
				textoOpcional(command.capacidad()),
				textoOpcional(command.remito()),
				textoOpcional(command.ordenCompra()),
				textoOpcional(command.proveedor()),
				textoOpcional(command.ubicacion()),
				textoOpcional(command.observaciones()),
				command.activo());
	}

	private StockComponenteDetalle toDetalle(StockComponente componente) {
		return new StockComponenteDetalle(
				componente.getId(),
				componente.getTipo(),
				componente.getEstado(),
				componente.getDescripcion(),
				componente.getMarca(),
				componente.getModelo(),
				componente.getSerial(),
				componente.getCapacidad(),
				componente.getRemito(),
				componente.getOrdenCompra(),
				componente.getProveedor(),
				componente.getUbicacion(),
				componente.getObservaciones(),
				componente.isActivo());
	}

	private String textoOpcional(String valor) {
		return StringUtils.hasText(valor) ? valor.trim() : null;
	}

	private String textoRequerido(String valor, String campo) {
		if (!StringUtils.hasText(valor)) {
			throw new IllegalArgumentException("El campo " + campo + " es obligatorio.");
		}
		return valor.trim();
	}

	public record GuardarStockComponenteCommand(
			TipoComponente tipo,
			EstadoStockComponente estado,
			String descripcion,
			String marca,
			String modelo,
			String serial,
			String capacidad,
			String remito,
			String ordenCompra,
			String proveedor,
			String ubicacion,
			String observaciones,
			boolean activo) {
	}

	public record StockComponenteDetalle(
			Long id,
			TipoComponente tipo,
			EstadoStockComponente estado,
			String descripcion,
			String marca,
			String modelo,
			String serial,
			String capacidad,
			String remito,
			String ordenCompra,
			String proveedor,
			String ubicacion,
			String observaciones,
			boolean activo) {
	}

	public static class StockComponenteNoEncontradoException extends RuntimeException {

		public StockComponenteNoEncontradoException(Long id) {
			super("Componente de stock no encontrado: " + id);
		}
	}

	public static class StockComponenteNoDisponibleException extends RuntimeException {

		public StockComponenteNoDisponibleException(Long id) {
			super("Componente de stock no disponible: " + id);
		}
	}

	public static class StockComponenteNoReservadoException extends RuntimeException {

		public StockComponenteNoReservadoException(Long id) {
			super("Componente de stock no reservado: " + id);
		}
	}
}
