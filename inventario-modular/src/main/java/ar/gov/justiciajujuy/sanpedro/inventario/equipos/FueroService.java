package ar.gov.justiciajujuy.sanpedro.inventario.equipos;

import java.time.Clock;
import java.time.Instant;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import ar.gov.justiciajujuy.sanpedro.inventario.security.ActiveDirectoryDomainService;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.Ubicacion;
import ar.gov.justiciajujuy.sanpedro.inventario.ubicaciones.UbicacionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * Servicio centralizado para la administración y resolución canónica de Fueros judiciales.
 * <p>
 * Combina:
 * 1. Unidades Organizativas (OUs) obtenidas directamente desde Active Directory.
 * 2. Mapeo de prefijos oficiales de equipos (DEFAULT_FUERO_MAPPING).
 * 3. Fueros asignados a Ubicaciones y Sedes.
 * 4. Fueros ya registrados en Equipos existentes.
 */
@Service
public class FueroService {

	public static final Map<String, String> DEFAULT_FUERO_MAPPING = Map.ofEntries(
			Map.entry("TTSIVVOC", "Tribunal de Trabajo Sala IV"),
			Map.entry("OGL", "Oficina de Gestion Laboral"),
			Map.entry("SISTEMAS", "Dpto. Informatica San Pedro"),
			Map.entry("VGS", "Violencia de Género 5"),
			Map.entry("VG5", "Violencia de Género 5"),
			Map.entry("SIVL", "Sala IV Laboral"),
			Map.entry("TJO1", "Tribunal de Juicio"),
			Map.entry("TJ01", "Tribunal de Juicio"),
			Map.entry("TJ", "Tribunal de Juicio"),
			Map.entry("CGESE", "Cámara Gesell"),
			Map.entry("JCC8SEC16", "Juzgado civil y Comercial N°8 Secretaria 16"),
			Map.entry("JCC9SEC18", "Juzgado civil y Comercial N°9 Secretaria 18"),
			Map.entry("JCC", "Juzgado Civil y Comercial"),
			Map.entry("CCYCSIV", "Cámara Civil y Comercial Sala IV"),
			Map.entry("CCYC", "Cámara Civil y Comercial"),
			Map.entry("PRENSA", "Prensa Poder Judicial de San Pedro de Jujuy"),
			Map.entry("SUPINT", "Superintendencia"),
			Map.entry("EQINT", "Equipo Interdisciplinario"),
			Map.entry("JUZMEN2", "Juzgado de Menores 2"),
			Map.entry("JUZMEN", "Juzgado de Menores"),
			Map.entry("JMEN", "Juzgado de Menores"),
			Map.entry("OGJ", "Oficina de Gestion Judicial"),
			Map.entry("VIOGEN", "Violencia de Género 5"),
			Map.entry("TFSIIIV", "Tribunal de Familia - Sala III"),
			Map.entry("TRIBJU", "Tribunal de Juicio"),
			Map.entry("FAM", "Juzgado de Familia"),
			Map.entry("JF", "Juzgado de Familia"),
			Map.entry("JFAM", "Juzgado de Familia"),
			Map.entry("CORP", "Juzgado de Control - Corp."),
			Map.entry("JCON", "Juzgado de Control"),
			Map.entry("OMN", "Mandamientos y Notificaciones"),
			Map.entry("OM", "Oficina de Mandamientos"),
			Map.entry("NOT", "Oficina de Notificaciones"),
			Map.entry("BIB", "Biblioteca"),
			Map.entry("ARQ", "Archivo"),
			Map.entry("INT", "Intendencia"),
			Map.entry("MAY", "Mayordomia"),
			Map.entry("MED", "Reconocimiento Medico"),
			Map.entry("PSI", "Psicologia"),
			Map.entry("TS", "Trabajo Social"),
			Map.entry("MESA", "Mesa de Entradas"),
			Map.entry("ME", "Mesa de Entradas"),
			Map.entry("VOC", "Vocalia"),
			Map.entry("DP", "Defensoria Publica"),
			Map.entry("DEF", "Defensoria"),
			Map.entry("MPA", "Ministerio Publico Acusacion"),
			Map.entry("SIGJ", "Sistemas SIGJ")
	);

	private static final long CACHE_TTL_SECONDS = 60;

	private final ActiveDirectoryDomainService activeDirectoryDomainService;
	private final UbicacionRepository ubicacionRepository;
	private final EquipoRepository equipoRepository;
	private final Clock clock;

	private volatile List<String> cachedFueros = null;
	private volatile Instant cacheLoadedAt = Instant.EPOCH;

	@Autowired
	public FueroService(
			ActiveDirectoryDomainService activeDirectoryDomainService,
			UbicacionRepository ubicacionRepository,
			EquipoRepository equipoRepository) {
		this(activeDirectoryDomainService, ubicacionRepository, equipoRepository, Clock.systemDefaultZone());
	}

	FueroService(
			ActiveDirectoryDomainService activeDirectoryDomainService,
			UbicacionRepository ubicacionRepository,
			EquipoRepository equipoRepository,
			Clock clock) {
		this.activeDirectoryDomainService = activeDirectoryDomainService;
		this.ubicacionRepository = ubicacionRepository;
		this.equipoRepository = equipoRepository;
		this.clock = clock;
	}

	/**
	 * Retorna la lista unificada, deduplicada y ordenada alfabéticamente de Fueros / Áreas disponibles.
	 */
	public List<String> listarFueros() {
		Instant now = Instant.now(clock);
		if (cachedFueros != null && cacheLoadedAt.plusSeconds(CACHE_TTL_SECONDS).isAfter(now)) {
			return cachedFueros;
		}

		Set<String> fueros = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);

		// 1. Unidades Organizativas desde Active Directory
		try {
			List<String> adOus = activeDirectoryDomainService.listarFuerosDesdeAd();
			fueros.addAll(adOus);
		} catch (Exception ignored) {
		}

		// 2. Fueros canónicos oficiales del Poder Judicial
		fueros.addAll(DEFAULT_FUERO_MAPPING.values());

		// 3. Fueros configurados en ubicaciones
		try {
			for (Ubicacion u : ubicacionRepository.findAll()) {
				if (StringUtils.hasText(u.getFuero())) {
					fueros.add(u.getFuero().trim());
				}
			}
		} catch (Exception ignored) {
		}

		// 4. Fueros existentes en equipos
		try {
			for (Equipo e : equipoRepository.findAll()) {
				if (StringUtils.hasText(e.getFuero())) {
					fueros.add(e.getFuero().trim());
				}
			}
		} catch (Exception ignored) {
		}

		List<String> resultado = List.copyOf(fueros);
		cachedFueros = resultado;
		cacheLoadedAt = now;
		return resultado;
	}

	/**
	 * Resuelve automáticamente el fuero de una máquina:
	 * 1. Si el script lo informó explícitamente, lo respeta.
	 * 2. Si no, consulta la OU del equipo en Active Directory.
	 * 3. Si no está en AD, detecta por prefijo de nombre.
	 */
	public String resolverFuero(String fueroReportado, String pcNombre) {
		if (StringUtils.hasText(fueroReportado)) {
			return fueroReportado.trim();
		}

		// Consulta en Active Directory
		try {
			String fueroAd = activeDirectoryDomainService.obtenerFueroDeEquipo(pcNombre);
			if (StringUtils.hasText(fueroAd)) {
				return fueroAd.trim();
			}
		} catch (Exception ignored) {
		}

		// Fallback a prefijo de nombre
		return detectarFueroPorPrefijo(pcNombre);
	}

	/**
	 * Detecta el fuero a partir del prefijo del nombre de la computadora.
	 */
	public String detectarFueroPorPrefijo(String pcNombre) {
		if (pcNombre == null) {
			return "Desconocido";
		}
		String pcUpper = pcNombre.toUpperCase();
		String bestMatch = "Desconocido";
		int longestPrefixLen = -1;

		for (Map.Entry<String, String> entry : DEFAULT_FUERO_MAPPING.entrySet()) {
			String prefix = entry.getKey().toUpperCase();
			if (pcUpper.startsWith(prefix)) {
				if (prefix.length() > longestPrefixLen) {
					longestPrefixLen = prefix.length();
					bestMatch = entry.getValue();
				}
			}
		}
		return bestMatch;
	}

	public void invalidarCache() {
		this.cachedFueros = null;
		this.cacheLoadedAt = Instant.EPOCH;
	}
}
