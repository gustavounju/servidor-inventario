package ar.gov.justiciajujuy.sanpedro.inventario.web;

import ar.gov.justiciajujuy.sanpedro.inventario.security.AuthorizationService;
import ar.gov.justiciajujuy.sanpedro.inventario.tareas.TareaAvisoService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ContentDisposition;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.server.ResponseStatusException;

@Controller
public class TareaMovilController {
    private final AuthorizationService authorization;
    private final TareaAvisoService avisos;
    private final FileSystemResource apk;

    public TareaMovilController(AuthorizationService authorization, TareaAvisoService avisos,
            @Value("${inventario.movil.apk-path:output/android/inventario-tareas-lan-piloto.apk}") String apkPath) {
        this.authorization = authorization;
        this.avisos = avisos;
        // La ruta es configuracion del servidor, nunca un parametro de descarga controlado por el cliente.
        this.apk = new FileSystemResource(apkPath);
    }

    @GetMapping("/movil/login")
    public String login() {
        return "movil/login";
    }

    @GetMapping({"/movil", "/movil/tareas"})
    public String tareas(@AuthenticationPrincipal UserDetails user, Model model) {
        exigirPermiso(user);
        model.addAttribute("apkDisponible", apk.isReadable());
        return "movil/tareas";
    }

    @GetMapping("/api/v1/movil/apk")
    public ResponseEntity<Resource> descargarApk(@AuthenticationPrincipal UserDetails user) {
        exigirPermiso(user);
        if (!apk.isReadable()) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "APK no disponible.");
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename(apk.getFilename()).build().toString())
                .header(HttpHeaders.CACHE_CONTROL, "no-store")
                .contentType(MediaType.parseMediaType("application/vnd.android.package-archive"))
                .body(apk);
    }

    @GetMapping("/api/v1/movil/sesion")
    @ResponseBody
    public SesionMovil sesion(@AuthenticationPrincipal UserDetails user, HttpServletResponse response) {
        exigirPermiso(user);
        response.setHeader("Cache-Control", "no-store");
        return new SesionMovil(authorization.obtenerUsuarioActual(user),
                authorization.tienePermiso(user, "TAREAS", "EDITAR"),
                authorization.puedeAdministrarUsuarios(user));
    }

    @GetMapping("/api/v1/movil/avisos")
    @ResponseBody
    public TareaAvisoService.LoteAvisos avisos(@AuthenticationPrincipal UserDetails user,
            @RequestParam(required = false) Long despuesDe, HttpServletResponse response) {
        exigirPermiso(user);
        if (despuesDe != null && despuesDe < 0) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cursor invalido.");
        }
        response.setHeader("Cache-Control", "no-store");
        return avisos.consultar(despuesDe);
    }

    private void exigirPermiso(UserDetails user) {
        if (!authorization.tienePermiso(user, "TAREAS", "VER")) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No tiene permiso para ver tareas.");
        }
    }

    public record SesionMovil(AuthorizationService.UsuarioActual usuario, boolean puedeEditar, boolean administrador) { }
}
