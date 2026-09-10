package ar.gov.justiciajujuy.sanpedro.inventario.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaAvisoService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaTecnicaService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.concurrent.Executors;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

@SpringBootTest(properties = { "inventario.local-auth.enabled=true", "inventario.local-auth.password=ClaveLocal123!" })
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Sql({"/sql/limpiar-seguridad-modular-test.sql", "/sql/seguridad-modular-test.sql"})
class TareaMovilControllerTests {
    @Autowired MockMvc mvc;
    @Autowired TareaTecnicaService tareas;
    @Autowired TareaAvisoService avisos;
    @Autowired JdbcTemplate jdbc;
    @Autowired PlatformTransactionManager transactions;
    @Autowired DataSource dataSource;

    private static final String NUEVA = """
            {"titulo":"Revisar impresora", "solicitanteUsername":"mesa", "solicitanteNombre":"Mesa de entradas",
             "solicitanteFuero":"Oficina", "prioridad":"ALTA"}
            """;

    @Test void ingresoMovilConservaDestinoYErrores() throws Exception {
        mvc.perform(get("/movil/tareas")).andExpect(redirectedUrl("/movil/login"));
        mvc.perform(get("/movil/login")).andExpect(status().isOk()).andExpect(content().string(containsString("name=\"destino\"")));
        mvc.perform(post("/login").with(csrf()).param("destino", "movil").param("username", "admin.local").param("password", "ClaveLocal123!"))
                .andExpect(redirectedUrl("/movil/tareas"));
        mvc.perform(post("/login").with(csrf()).param("destino", "movil").param("username", "admin.local").param("password", "invalida"))
                .andExpect(redirectedUrl("/movil/login?error"));
        mvc.perform(post("/login").with(csrf()).param("destino", "https://externo.test").param("username", "admin.local").param("password", "ClaveLocal123!"))
                .andExpect(redirectedUrl("/admin"));
    }

    @Test void pantallaIndependienteYPermisos() throws Exception {
        mvc.perform(get("/movil/tareas").with(user("admin.local"))).andExpect(status().isOk())
                .andExpect(content().string(containsString("Nueva tarea"))).andExpect(content().string(not(containsString("app-sidebar"))));
        mvc.perform(get("/api/v1/movil/sesion").with(user("admin.local"))).andExpect(status().isOk())
                .andExpect(jsonPath("$.usuario.username").value("admin.local")).andExpect(jsonPath("$.puedeEditar").value(true));
        mvc.perform(get("/api/v1/movil/avisos")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/movil/apk")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/movil/apk").with(user("sin.permisos"))).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/movil/avisos").with(user("sin.permisos"))).andExpect(status().isForbidden());
        mvc.perform(get("/movil/tareas").with(user("sin.permisos"))).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/movil/avisos?despuesDe=-1").with(user("admin.local"))).andExpect(status().isBadRequest());
        mvc.perform(post("/api/v1/tareas-tecnicas").with(user("admin.local")).contentType(MediaType.APPLICATION_JSON).content(NUEVA))
                .andExpect(status().isForbidden());
    }

    @Test void creacionDesdeApiGeneraAvisoRecuperableSinDuplicar() throws Exception {
        mvc.perform(get("/api/v1/movil/avisos").with(user("admin.local")))
                .andExpect(jsonPath("$.siguiente").value(0)).andExpect(jsonPath("$.avisos").isEmpty());
        mvc.perform(post("/api/v1/tareas-tecnicas").with(user("admin.local")).with(csrf()).contentType(MediaType.APPLICATION_JSON).content(NUEVA))
                .andExpect(status().isCreated());
        mvc.perform(get("/api/v1/movil/avisos?despuesDe=0").with(user("admin.local")))
                .andExpect(jsonPath("$.avisos.length()").value(1)).andExpect(jsonPath("$.avisos[0].titulo").value("Revisar impresora"))
                .andExpect(jsonPath("$.avisos[0].autor").value("admin.local")).andExpect(header().string("Cache-Control", "no-store"));
        mvc.perform(get("/api/v1/movil/avisos?despuesDe=1").with(user("admin.local"))).andExpect(jsonPath("$.avisos").isEmpty());
        // Inicializar un telefono nuevo no hace sonar todas las tareas anteriores.
        mvc.perform(get("/api/v1/movil/avisos").with(user("admin.local"))).andExpect(jsonPath("$.siguiente").value(1)).andExpect(jsonPath("$.avisos").isEmpty());
        new ResourceDatabasePopulator(new ClassPathResource("db/migration/V15__avisos_tareas_lan.sql")).execute(dataSource);
        assertThat(avisos.consultar(0L).avisos()).hasSize(1);
    }

    @Test void rollbackDeTareaNoDejaAvisosFantasma() {
        long total = tareas.contar();
        new TransactionTemplate(transactions).executeWithoutResult(tx -> {
            tareas.crear(new TareaTecnicaService.GuardarTareaTecnicaCommand(1L, "No confirmar", null, "mesa", "Mesa", "Oficina", null, null, "admin.local"));
            tx.setRollbackOnly();
        });
        assertThat(tareas.contar()).isEqualTo(total);
        assertThat(avisos.consultar(0L).avisos()).isEmpty();
        assertThat(avisos.consultar(null).siguiente()).isZero();
    }

    @Test void paginaAvisosEnOrdenYRecuperaCursorDeBaseRestaurada() {
        for (long i = 1; i <= 105; i++) {
            jdbc.update("INSERT INTO tareas_avisos (id,tarea_id,titulo,autor) VALUES (?,?,?,?)", i, 1L, "Tarea", "admin.local");
        }
        jdbc.update("UPDATE tareas_aviso_secuencia SET ultimo_id = 105 WHERE id = 1");
        var primera = avisos.consultar(0L);
        assertThat(primera.avisos()).hasSize(100);
        assertThat(primera.siguiente()).isEqualTo(100);
        assertThat(avisos.consultar(primera.siguiente()).avisos()).hasSize(5);
        assertThat(avisos.consultar(900L).siguiente()).isEqualTo(105);
    }

    @Test void dosTecnicosNoPuedenTomarLaMismaTarea() throws Exception {
        var creada = tareas.crear(new TareaTecnicaService.GuardarTareaTecnicaCommand(1L, "Concurrente", null, "mesa", "Mesa", "Oficina", null, null, "admin.local"));
        CountDownLatch inicio = new CountDownLatch(1);
        try (var workers = Executors.newFixedThreadPool(2)) {
            var uno = workers.submit(() -> tomarAlMismoTiempo(inicio, creada.id(), "tecnico.uno"));
            var dos = workers.submit(() -> tomarAlMismoTiempo(inicio, creada.id(), "tecnico.dos"));
            inicio.countDown();
            assertThat(uno.get(10, TimeUnit.SECONDS) + dos.get(10, TimeUnit.SECONDS)).isEqualTo(1);
        }
    }

    @Test void tareaFinalizadaNoPuedeVolverATomarse() throws Exception {
        tareas.cambiarEstado(1L, new TareaTecnicaService.CambiarEstadoTareaCommand(ar.gov.justiciajujuy.sanpedro.inventario.tareas.EstadoTareaTecnica.CERRADA, "Resuelta"));
        mvc.perform(post("/api/v1/tareas-tecnicas/1/tomar").with(user("admin.local")).with(csrf())).andExpect(status().isConflict());
    }

    private int tomarAlMismoTiempo(CountDownLatch inicio, Long id, String username) throws Exception {
        inicio.await(5, TimeUnit.SECONDS);
        try { tareas.tomar(id, username); return 1; }
        catch (TareaTecnicaService.TareaTecnicaYaAsignadaException expected) { return 0; }
    }
}
