package ar.gov.justiciajujuy.sanpedro.inventario.armado;

import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.auditoria.AuditoriaService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.ComponenteDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.ComponenteService.GuardarComponenteCommand;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.EstadoComparacion;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.OrigenComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.componentes.TipoComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoService.EquipoNoEncontradoException;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.EstadoStockComponente;
import ar.gov.justiciajujuy.sanpedro.inventario.stock.StockService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class OrdenArmadoService {

	private final OrdenArmadoRepository ordenArmadoRepository;
	private final OrdenArmadoComponenteRepository ordenArmadoComponenteRepository;
	private final EquipoRepository equipoRepository;
	private final ComponenteService componenteService;
	private final StockService stockService;
	private final AuditoriaService auditoriaService;

	public OrdenArmadoService(
			OrdenArmadoRepository ordenArmadoRepository,
			OrdenArmadoComponenteRepository ordenArmadoComponenteRepository,
			EquipoRepository equipoRepository,
			ComponenteService componenteService,
			StockService stockService,
			AuditoriaService auditoriaService) {
		this.ordenArmadoRepository = ordenArmadoRepository;
		this.ordenArmadoComponenteRepository = ordenArmadoComponenteRepository;
		this.equipoRepository = equipoRepository;
		this.componenteService = componenteService;
		this.stockService = stockService;
		this.auditoriaService = auditoriaService;
	}

	@Transactional(readOnly = true)
	public List<OrdenArmadoDetalle> listarTodas() {
		return ordenArmadoRepository.findAllByOrderByIdDesc().stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional(readOnly = true)
	public List<OrdenArmadoDetalle> listarPorEquipo(Long equipoId) {
		return ordenArmadoRepository.findByEquipoIdOrderByIdDesc(equipoId).stream()
				.map(this::toDetalle)
				.toList();
	}

	@Transactional
	public OrdenArmadoDetalle crear(Long equipoId, GuardarOrdenArmadoCommand command) {
		Equipo equipo = equipoRepository.findById(equipoId)
				.orElseThrow(() -> new EquipoNoEncontradoException(equipoId));
		OrdenArmado orden = new OrdenArmado(equipo, textoRequerido(command.descripcion(), "descripcion"));
		orden.actualizar(command.estado(), textoRequerido(command.descripcion(), "descripcion"), textoOpcional(command.observaciones()));
		OrdenArmado guardada = ordenArmadoRepository.save(orden);
		auditoriaService.registrar("ORDENES_ARMADO", "CREAR", "OrdenArmado", guardada.getId(),
				"Orden de armado creada para " + equipo.getNombre() + " con estado " + guardada.getEstado() + ".");
		return toDetalle(guardada);
	}

	@Transactional
	public OrdenArmadoDetalle actualizar(Long id, GuardarOrdenArmadoCommand command) {
		OrdenArmado orden = ordenArmadoRepository.findById(id)
				.orElseThrow(() -> new OrdenArmadoNoEncontradaException(id));
		orden.actualizar(command.estado(), textoRequerido(command.descripcion(), "descripcion"), textoOpcional(command.observaciones()));
		OrdenArmado guardada = ordenArmadoRepository.save(orden);
		auditoriaService.registrar("ORDENES_ARMADO", "ACTUALIZAR", "OrdenArmado", guardada.getId(),
				"Orden de armado actualizada con estado " + guardada.getEstado() + ".");
		return toDetalle(guardada);
	}

	@Transactional
	public void eliminar(Long id) {
		OrdenArmado orden = ordenArmadoRepository.findById(id)
				.orElseThrow(() -> new OrdenArmadoNoEncontradaException(id));

		List<OrdenArmadoComponente> componentes = ordenArmadoComponenteRepository.findByOrdenId(id);
		for (OrdenArmadoComponente oac : componentes) {
			if (oac.getStockComponente() != null && oac.getStockComponente().getEstado() == EstadoStockComponente.RESERVADO) {
				oac.getStockComponente().liberar();
			}
		}
		ordenArmadoComponenteRepository.deleteByOrdenId(id);
		ordenArmadoRepository.delete(orden);
		auditoriaService.registrar("ORDENES_ARMADO", "ELIMINAR", "OrdenArmado", id,
				"Orden de armado " + id + " eliminada.");
	}

	/**
	 * Incorpora un componente previsto (esperado) al gemelo digital del equipo asociado a la orden.
	 * Si se seleccionó una pieza física de Stock, la reserva automáticamente y propaga sus datos
	 * de trazabilidad de compras (Remito, Orden de Compra y Proveedor).
	 *
	 * @param ordenId ID de la orden de armado
	 * @param command Datos del componente y referencia opcional al ítem de stock
	 * @return Detalle del componente creado en el gemelo digital
	 */
	@Transactional
	public ComponenteDetalle agregarComponenteEsperado(Long ordenId, GuardarComponenteOrdenCommand command) {
		OrdenArmado orden = ordenArmadoRepository.findById(ordenId)
				.orElseThrow(() -> new OrdenArmadoNoEncontradaException(ordenId));
		StockComponente stock = command.stockComponenteId() != null ? stockService.reservar(command.stockComponenteId()) : null;
		String remito = stock != null && StringUtils.hasText(stock.getRemito()) ? stock.getRemito() : command.remito();
		String ordenCompra = stock != null && StringUtils.hasText(stock.getOrdenCompra()) ? stock.getOrdenCompra() : command.ordenCompra();
		String proveedor = stock != null && StringUtils.hasText(stock.getProveedor()) ? stock.getProveedor() : command.proveedor();

		ComponenteDetalle componente = componenteService.crear(orden.getEquipo().getId(), new GuardarComponenteCommand(
				command.tipo(),
				OrigenComponente.ORDEN_ARMADO,
				EstadoComparacion.ESPERADO,
				textoRequerido(command.descripcion(), "descripcion"),
				command.marca(),
				command.modelo(),
				command.serial(),
				command.capacidad(),
				remito,
				ordenCompra,
				proveedor,
				command.ubicacion(),
				command.observaciones(),
				true));
		OrdenArmadoComponente ordenComponente = ordenArmadoComponenteRepository.save(new OrdenArmadoComponente(
				orden,
				componenteService.obtenerEntidad(componente.id()),
				stock));
		auditoriaService.registrar("ORDENES_ARMADO", "AGREGAR_COMPONENTE", "OrdenArmadoComponente", ordenComponente.getId(),
				"Componente esperado agregado a orden " + orden.getId() + (stock != null ? " con stock reservado." : " sin stock asociado."));
		return componente;
	}

	@Transactional(readOnly = true)
	public List<OrdenArmadoComponenteDetalle> listarComponentesPorEquipo(Long equipoId) {
		return ordenArmadoComponenteRepository.findByOrdenEquipoIdOrderByIdAsc(equipoId).stream()
				.map(this::toComponenteDetalle)
				.toList();
	}

	/**
	 * Confirma la salida física de un componente reservado en Stock hacia la PC ensamblada.
	 * Transiciona el stock a estado ASIGNADO y asegura la propagación definitiva de los campos
	 * de remito, orden de compra y proveedor al componente del gemelo digital.
	 *
	 * @param ordenComponenteId ID del vínculo orden-componente
	 * @return Componente actualizado con estado ORIGEN_STOCK y trazabilidad de compras
	 */
	@Transactional
	public ComponenteDetalle confirmarSalidaStock(Long ordenComponenteId) {
		OrdenArmadoComponente ordenComponente = ordenArmadoComponenteRepository.findById(ordenComponenteId)
				.orElseThrow(() -> new OrdenArmadoComponenteNoEncontradoException(ordenComponenteId));
		StockComponente stock = ordenComponente.getStockComponente();
		if (stock == null) {
			throw new OrdenArmadoComponenteSinStockException(ordenComponenteId);
		}
		stockService.asignarReservado(stock.getId());
		var componente = ordenComponente.getComponente();
		String remito = stock.getRemito() != null ? stock.getRemito() : componente.getRemito();
		String ordenCompra = stock.getOrdenCompra() != null ? stock.getOrdenCompra() : componente.getOrdenCompra();
		String proveedor = stock.getProveedor() != null ? stock.getProveedor() : componente.getProveedor();

		ComponenteDetalle actualizado = componenteService.actualizar(componente.getId(), new GuardarComponenteCommand(
				componente.getTipo(),
				OrigenComponente.STOCK,
				EstadoComparacion.ESPERADO,
				componente.getDescripcion(),
				componente.getMarca(),
				componente.getModelo(),
				componente.getSerial(),
				componente.getCapacidad(),
				remito,
				ordenCompra,
				proveedor,
				componente.getUbicacion(),
				observacionSalidaStock(componente.getObservaciones()),
				componente.isActivo()));
		auditoriaService.registrar("ORDENES_ARMADO", "CONFIRMAR_SALIDA_STOCK", "OrdenArmadoComponente", ordenComponente.getId(),
				"Salida real desde stock confirmada para orden " + ordenComponente.getOrden().getId() + ".");
		return actualizado;
	}

	private OrdenArmadoDetalle toDetalle(OrdenArmado orden) {
		return new OrdenArmadoDetalle(
				orden.getId(),
				orden.getEquipo().getId(),
				orden.getEquipo().getNombre(),
				orden.getEstado(),
				orden.getDescripcion(),
				orden.getObservaciones());
	}

	private OrdenArmadoComponenteDetalle toComponenteDetalle(OrdenArmadoComponente ordenComponente) {
		var componente = ordenComponente.getComponente();
		var stock = ordenComponente.getStockComponente();
		return new OrdenArmadoComponenteDetalle(
				ordenComponente.getId(),
				ordenComponente.getOrden().getId(),
				componente.getId(),
				stock != null ? stock.getId() : null,
				componente.getTipo(),
				componente.getDescripcion(),
				componente.getSerial(),
				componente.getOrigen(),
				componente.getEstadoComparacion(),
				stock != null ? stock.getEstado() : null,
				componente.getRemito(),
				componente.getOrdenCompra(),
				componente.getProveedor());
	}

	private String observacionSalidaStock(String observacionesActuales) {
		String salida = "Salida real desde stock confirmada.";
		if (!StringUtils.hasText(observacionesActuales)) {
			return salida;
		}
		if (observacionesActuales.contains(salida)) {
			return observacionesActuales;
		}
		return observacionesActuales.trim() + " " + salida;
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

	public record GuardarOrdenArmadoCommand(
			EstadoOrdenArmado estado,
			String descripcion,
			String observaciones) {
	}

	public record GuardarComponenteOrdenCommand(
			Long stockComponenteId,
			TipoComponente tipo,
			String descripcion,
			String marca,
			String modelo,
			String serial,
			String capacidad,
			String ubicacion,
			String observaciones,
			String remito,
			String ordenCompra,
			String proveedor) {
	}

	public record OrdenArmadoDetalle(
			Long id,
			Long equipoId,
			String equipoNombre,
			EstadoOrdenArmado estado,
			String descripcion,
			String observaciones) {
	}

	public record OrdenArmadoComponenteDetalle(
			Long id,
			Long ordenId,
			Long componenteId,
			Long stockComponenteId,
			TipoComponente tipo,
			String descripcion,
			String serial,
			OrigenComponente origen,
			EstadoComparacion estadoComparacion,
			EstadoStockComponente estadoStock,
			String remito,
			String ordenCompra,
			String proveedor) {
	}

	public static class OrdenArmadoNoEncontradaException extends RuntimeException {

		public OrdenArmadoNoEncontradaException(Long id) {
			super("Orden de armado no encontrada: " + id);
		}
	}

	public static class OrdenArmadoComponenteNoEncontradoException extends RuntimeException {

		public OrdenArmadoComponenteNoEncontradoException(Long id) {
			super("Componente de orden de armado no encontrado: " + id);
		}
	}

	public static class OrdenArmadoComponenteSinStockException extends RuntimeException {

		public OrdenArmadoComponenteSinStockException(Long id) {
			super("Componente de orden sin stock asociado: " + id);
		}
	}
}
