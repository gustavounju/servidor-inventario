package ar.gov.justiciajujuy.sanpedro.inventario.reportes;

import java.util.Arrays;
import java.util.List;

import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService;
import ar.gov.justiciajujuy.sanpedro.inventario.actas.ActaService.ActaDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService;
import ar.gov.justiciajujuy.sanpedro.inventario.muebles.MuebleService.MuebleDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService;
import ar.gov.justiciajujuy.sanpedro.inventario.patrimonio.PatrimonioService.BienPatrimonialDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService.TareaTecnicaDetalle;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionService.UbicacionDetalle;
import org.springframework.stereotype.Service;

@Service
public class ReporteService {

	private final EquipoRepository equipoRepository;
	private final MuebleService muebleService;
	private final PatrimonioService patrimonioService;
	private final TareaTecnicaService tareaTecnicaService;
	private final ActaService actaService;
	private final UbicacionService ubicacionService;

	public ReporteService(EquipoRepository equipoRepository, MuebleService muebleService,
			PatrimonioService patrimonioService, TareaTecnicaService tareaTecnicaService, ActaService actaService,
			UbicacionService ubicacionService) {
		this.equipoRepository = equipoRepository;
		this.muebleService = muebleService;
		this.patrimonioService = patrimonioService;
		this.tareaTecnicaService = tareaTecnicaService;
		this.actaService = actaService;
		this.ubicacionService = ubicacionService;
	}

	public ResumenOperativo resumen() {
		return new ResumenOperativo(
				equipoRepository.count(),
				muebleService.contar(),
				patrimonioService.contar(),
				tareaTecnicaService.contar(),
				actaService.contar(),
				ubicacionService.contar());
	}

	public String mueblesCsv(String query) {
		StringBuilder csv = new StringBuilder("codigo,tipo,descripcion,ubicacion,fuero,responsable,estado,activo\n");
		for (MuebleDetalle mueble : muebleService.buscar(query, null)) {
			csv.append(fila(Arrays.asList(
					mueble.codigo(),
					mueble.tipo(),
					mueble.descripcion(),
					mueble.ubicacion(),
					mueble.fuero(),
					mueble.responsable(),
					String.valueOf(mueble.estado()),
					String.valueOf(mueble.activo()))));
		}
		return csv.toString();
	}

	public String patrimonioCsv(String query) {
		StringBuilder csv = new StringBuilder("numeroPatrimonial,categoria,descripcion,ubicacion,fuero,custodio,estado,equipoNombre,activo\n");
		for (BienPatrimonialDetalle bien : patrimonioService.buscar(query, null)) {
			csv.append(fila(Arrays.asList(
					bien.numeroPatrimonial(),
					bien.categoria(),
					bien.descripcion(),
					bien.ubicacion(),
					bien.fuero(),
					bien.custodio(),
					String.valueOf(bien.estado()),
					bien.equipoNombre(),
					String.valueOf(bien.activo()))));
		}
		return csv.toString();
	}

	public String tareasCsv(String query) {
		StringBuilder csv = new StringBuilder("id,titulo,equipoNombre,estado,prioridad,responsable\n");
		for (TareaTecnicaDetalle tarea : tareaTecnicaService.buscar(null, null, query)) {
			csv.append(fila(Arrays.asList(
					String.valueOf(tarea.id()),
					tarea.titulo(),
					tarea.equipoNombre(),
					String.valueOf(tarea.estado()),
					String.valueOf(tarea.prioridad()),
					tarea.responsable())));
		}
		return csv.toString();
	}

	public String actasCsv(String query) {
		StringBuilder csv = new StringBuilder("numero,tipo,equipoNombre,fechaEmision,destinatario,responsableEntrega,responsableRecepcion,estado,activo\n");
		for (ActaDetalle acta : actaService.buscar(query, null, null)) {
			csv.append(fila(Arrays.asList(
					acta.numero(),
					String.valueOf(acta.tipo()),
					acta.equipoNombre(),
					acta.fechaEmision() == null ? null : String.valueOf(acta.fechaEmision()),
					acta.destinatario(),
					acta.responsableEntrega(),
					acta.responsableRecepcion(),
					String.valueOf(acta.estado()),
					String.valueOf(acta.activo()))));
		}
		return csv.toString();
	}

	public String ubicacionesCsv(String query) {
		StringBuilder csv = new StringBuilder("codigo,nombre,tipo,fuero,responsable,edificio,piso,estado,activo\n");
		for (UbicacionDetalle ubicacion : ubicacionService.buscar(query, null, null)) {
			csv.append(fila(Arrays.asList(
					ubicacion.codigo(),
					ubicacion.nombre(),
					String.valueOf(ubicacion.tipo()),
					ubicacion.fuero(),
					ubicacion.responsable(),
					ubicacion.edificio(),
					ubicacion.piso(),
					String.valueOf(ubicacion.estado()),
					String.valueOf(ubicacion.activo()))));
		}
		return csv.toString();
	}

	private String fila(List<String> valores) {
		return valores.stream()
				.map(this::csv)
				.reduce((a, b) -> a + "," + b)
				.orElse("") + "\n";
	}

	private String csv(String valor) {
		if (valor == null) {
			return "";
		}
		String limpio = valor.replace("\"", "\"\"");
		return limpio.contains(",") || limpio.contains("\"") || limpio.contains("\n") ? "\"" + limpio + "\"" : limpio;
	}

	public record ResumenOperativo(long equipos, long muebles, long bienesPatrimoniales, long tareas, long actas,
			long ubicaciones) {
	}
}
