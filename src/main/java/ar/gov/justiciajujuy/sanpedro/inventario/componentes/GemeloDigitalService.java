package ar.gov.justiciajujuy.sanpedro.inventario.componentes;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
public class GemeloDigitalService {

	private final ComponenteRepository componenteRepository;
	private final EquipoRepository equipoRepository;

	public GemeloDigitalService(ComponenteRepository componenteRepository, EquipoRepository equipoRepository) {
		this.componenteRepository = componenteRepository;
		this.equipoRepository = equipoRepository;
	}

	@Transactional(readOnly = true)
	public List<ComparacionComponente> compararEquipo(Long equipoId) {
		List<Componente> componentes = componenteRepository.findByEquipoIdOrderByTipoAscDescripcionAsc(equipoId).stream()
				.filter(Componente::isActivo)
				.toList();
		List<Componente> esperados = componentes.stream()
				.filter(this::esEsperado)
				.toList();
		List<Componente> detectados = componentes.stream()
				.filter(this::esDetectado)
				.toList();
		List<ComparacionComponente> resultado = new ArrayList<>();
		List<Componente> detectadosPendientes = new ArrayList<>(detectados);

		for (Componente esperado : esperados) {
			Componente detectado = detectadosPendientes.stream()
					.filter(candidato -> coincideConCerteza(esperado, candidato))
					.findFirst()
					.orElse(null);
			if (detectado != null) {
				detectadosPendientes.remove(detectado);
				resultado.add(new ComparacionComponente(
						esperado.getTipo(),
						texto(esperado),
						texto(detectado),
						EstadoComparacion.COINCIDE,
						"El componente esperado aparece en el reporte o relevamiento."));
				continue;
			}

			Componente candidatoRevision = detectadosPendientes.stream()
					.filter(candidato -> requiereRevision(esperado, candidato))
					.findFirst()
					.orElse(null);
			if (candidatoRevision != null) {
				detectadosPendientes.remove(candidatoRevision);
				resultado.add(new ComparacionComponente(
						esperado.getTipo(),
						texto(esperado),
						texto(candidatoRevision),
						EstadoComparacion.REVISAR,
						"Hay un componente del mismo tipo con datos parecidos, pero falta confirmar serial, modelo o capacidad."));
				continue;
			}

			resultado.add(new ComparacionComponente(
					esperado.getTipo(),
					texto(esperado),
					"Sin detectar",
					EstadoComparacion.FALTA,
					"Estaba esperado por orden/stock, pero no aparece detectado."));
		}

		for (Componente detectado : detectadosPendientes) {
			resultado.add(new ComparacionComponente(
					detectado.getTipo(),
					"Sin esperar",
					texto(detectado),
					EstadoComparacion.SOBRA,
					"Aparece detectado, pero todavia no esta en una orden de armado o salida de stock."));
		}
		return resultado;
	}

	@Transactional(readOnly = true)
	public DashboardDiferencias dashboardDiferencias() {
		return dashboardDiferencias(null, null, null);
	}

	@Transactional(readOnly = true)
	public DashboardDiferencias dashboardDiferencias(String equipoQuery, String fuero, EstadoComparacion estado) {
		Map<EstadoComparacion, Long> totales = conteosIniciales();
		List<EquipoConDiferencias> equiposConDiferencias = new ArrayList<>();
		String equipoFiltro = normalizarFiltro(equipoQuery);
		String fueroFiltro = normalizarFiltro(fuero);

		for (Equipo equipo : equipoRepository.findAll(Sort.by("nombre"))) {
			if (!coincideEquipo(equipo, equipoFiltro, fueroFiltro)) {
				continue;
			}
			List<ComparacionComponente> comparacion = compararEquipo(equipo.getId());
			Map<EstadoComparacion, Long> conteosEquipo = conteosIniciales();
			List<DiferenciaDetalle> diferencias = new ArrayList<>();

			for (ComparacionComponente fila : comparacion) {
				if (estado != null && fila.resultado() != estado) {
					continue;
				}
				incrementar(totales, fila.resultado());
				incrementar(conteosEquipo, fila.resultado());
				if (fila.resultado() != EstadoComparacion.COINCIDE) {
					diferencias.add(new DiferenciaDetalle(
							fila.tipo(),
							fila.esperado(),
							fila.detectado(),
							fila.resultado(),
							fila.observacion()));
				}
			}

			if (!diferencias.isEmpty()) {
				long faltaEquipo = conteo(conteosEquipo, EstadoComparacion.FALTA);
				long sobraEquipo = conteo(conteosEquipo, EstadoComparacion.SOBRA);
				long revisarEquipo = conteo(conteosEquipo, EstadoComparacion.REVISAR);
				equiposConDiferencias.add(new EquipoConDiferencias(
						equipo.getId(),
						equipo.getNombre(),
						equipo.getFuero(),
						faltaEquipo,
						sobraEquipo,
						revisarEquipo,
						faltaEquipo + sobraEquipo + revisarEquipo,
						diferencias));
			}
		}

		long falta = conteo(totales, EstadoComparacion.FALTA);
		long sobra = conteo(totales, EstadoComparacion.SOBRA);
		long revisar = conteo(totales, EstadoComparacion.REVISAR);
		long coincide = conteo(totales, EstadoComparacion.COINCIDE);
		ConteoDiferencias conteo = new ConteoDiferencias(
				falta,
				sobra,
				revisar,
				coincide,
				falta + sobra + revisar,
				falta + sobra + revisar + coincide);
		return new DashboardDiferencias(conteo, equiposConDiferencias);
	}

	@Transactional(readOnly = true)
	public String dashboardDiferenciasCsv(String equipoQuery, String fuero, EstadoComparacion estado) {
		StringBuilder csv = new StringBuilder("equipo,fuero,tipo,resultado,esperado,detectado,observacion\n");
		DashboardDiferencias dashboard = dashboardDiferencias(equipoQuery, fuero, estado);
		for (EquipoConDiferencias equipo : dashboard.equipos()) {
			for (DiferenciaDetalle diferencia : equipo.diferencias()) {
				csv.append(fila(List.of(
						equipo.equipoNombre(),
						valor(equipo.fuero()),
						String.valueOf(diferencia.tipo()),
						String.valueOf(diferencia.resultado()),
						diferencia.esperado(),
						diferencia.detectado(),
						diferencia.observacion())));
			}
		}
		return csv.toString();
	}

	private boolean coincideEquipo(Equipo equipo, String equipoFiltro, String fueroFiltro) {
		return contiene(equipo.getNombre(), equipoFiltro) && contiene(equipo.getFuero(), fueroFiltro);
	}

	private boolean contiene(String valor, String filtro) {
		return !StringUtils.hasText(filtro) || (valor != null && normalizarTexto(valor).contains(filtro));
	}

	private String normalizarFiltro(String valor) {
		if (!StringUtils.hasText(valor)) {
			return null;
		}
		return normalizarTexto(valor);
	}

	private Map<EstadoComparacion, Long> conteosIniciales() {
		Map<EstadoComparacion, Long> conteos = new EnumMap<>(EstadoComparacion.class);
		for (EstadoComparacion estado : EstadoComparacion.values()) {
			conteos.put(estado, 0L);
		}
		return conteos;
	}

	private void incrementar(Map<EstadoComparacion, Long> conteos, EstadoComparacion estado) {
		conteos.computeIfPresent(estado, (clave, valor) -> valor + 1);
	}

	private long conteo(Map<EstadoComparacion, Long> conteos, EstadoComparacion estado) {
		return conteos.getOrDefault(estado, 0L);
	}

	private boolean esEsperado(Componente componente) {
		return componente.getEstadoComparacion() == EstadoComparacion.ESPERADO ||
				componente.getOrigen() == OrigenComponente.ORDEN_ARMADO ||
				componente.getOrigen() == OrigenComponente.STOCK ||
				componente.getOrigen() == OrigenComponente.RELEVAMIENTO_INICIAL;
	}

	private boolean esDetectado(Componente componente) {
		return componente.getOrigen() == OrigenComponente.SCRIPT;
	}

	private boolean coincideConCerteza(Componente esperado, Componente detectado) {
		if (esperado.getTipo() != detectado.getTipo()) {
			return false;
		}
		if (StringUtils.hasText(esperado.getSerial()) && StringUtils.hasText(detectado.getSerial())) {
			return normalizarIdentificador(esperado.getSerial()).equals(normalizarIdentificador(detectado.getSerial()));
		}
		if (StringUtils.hasText(esperado.getSerial()) || StringUtils.hasText(detectado.getSerial())) {
			return false;
		}
		return coincideTextoFuerte(esperado.getModelo(), detectado.getModelo()) ||
				coincideTextoFuerte(esperado.getDescripcion(), detectado.getDescripcion()) ||
				(coincideTextoFuerte(esperado.getCapacidad(), detectado.getCapacidad()) &&
						(coincideTextoFlexible(esperado.getModelo(), detectado.getModelo()) ||
								coincideTextoFlexible(esperado.getDescripcion(), detectado.getDescripcion())));
	}

	private boolean requiereRevision(Componente esperado, Componente detectado) {
		if (esperado.getTipo() != detectado.getTipo()) {
			return false;
		}
		if (StringUtils.hasText(esperado.getSerial()) && StringUtils.hasText(detectado.getSerial())) {
			return !normalizarIdentificador(esperado.getSerial()).equals(normalizarIdentificador(detectado.getSerial())) &&
					(coincideTextoFlexible(esperado.getModelo(), detectado.getModelo()) ||
							coincideTextoFlexible(esperado.getCapacidad(), detectado.getCapacidad()));
		}
		return coincideTextoFlexible(esperado.getModelo(), detectado.getModelo()) ||
				coincideTextoFlexible(esperado.getCapacidad(), detectado.getCapacidad()) ||
				coincideTextoFlexible(esperado.getDescripcion(), detectado.getDescripcion());
	}

	private boolean coincideTextoFuerte(String izquierdo, String derecho) {
		if (!StringUtils.hasText(izquierdo) || !StringUtils.hasText(derecho)) {
			return false;
		}
		return normalizarTexto(izquierdo).equals(normalizarTexto(derecho));
	}

	private boolean coincideTextoFlexible(String izquierdo, String derecho) {
		if (!StringUtils.hasText(izquierdo) || !StringUtils.hasText(derecho)) {
			return false;
		}
		String normalizadoIzquierdo = normalizarTexto(izquierdo);
		String normalizadoDerecho = normalizarTexto(derecho);
		return normalizadoIzquierdo.equals(normalizadoDerecho) ||
				normalizadoIzquierdo.contains(normalizadoDerecho) ||
				normalizadoDerecho.contains(normalizadoIzquierdo);
	}

	private String normalizarIdentificador(String valor) {
		return normalizarTexto(valor).replaceAll("[^a-z0-9]", "");
	}

	private String normalizarTexto(String valor) {
		return valor.trim().toLowerCase(Locale.ROOT).replaceAll("\\s+", " ");
	}

	private String texto(Componente componente) {
		List<String> partes = new ArrayList<>();
		partes.add(componente.getDescripcion());
		if (StringUtils.hasText(componente.getMarca())) {
			partes.add(componente.getMarca());
		}
		if (StringUtils.hasText(componente.getModelo())) {
			partes.add(componente.getModelo());
		}
		if (StringUtils.hasText(componente.getSerial())) {
			partes.add("SN " + componente.getSerial());
		}
		if (StringUtils.hasText(componente.getCapacidad())) {
			partes.add(componente.getCapacidad());
		}
		return String.join(" / ", partes);
	}

	private String valor(String valor) {
		return valor == null ? "" : valor;
	}

	private String fila(List<String> valores) {
		return valores.stream()
				.map(this::csv)
				.reduce((a, b) -> a + "," + b)
				.orElse("") + "\n";
	}

	private String csv(String valor) {
		String limpio = valor == null ? "" : valor.replace("\"", "\"\"");
		return limpio.contains(",") || limpio.contains("\"") || limpio.contains("\n") ? "\"" + limpio + "\"" : limpio;
	}

	public record ComparacionComponente(
			TipoComponente tipo,
			String esperado,
			String detectado,
			EstadoComparacion resultado,
			String observacion) {
	}

	public record DashboardDiferencias(
			ConteoDiferencias conteo,
			List<EquipoConDiferencias> equipos) {
	}

	public record ConteoDiferencias(
			long falta,
			long sobra,
			long revisar,
			long coincide,
			long pendientes,
			long total) {
	}

	public record EquipoConDiferencias(
			Long equipoId,
			String equipoNombre,
			String fuero,
			long falta,
			long sobra,
			long revisar,
			long pendientes,
			List<DiferenciaDetalle> diferencias) {
	}

	public record DiferenciaDetalle(
			TipoComponente tipo,
			String esperado,
			String detectado,
			EstadoComparacion resultado,
			String observacion) {
	}
}
