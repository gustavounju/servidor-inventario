package ar.gov.justiciajujuy.sanpedro.inventario.auditoria;

import ar.gov.justiciajujuy.sanpedro.inventario.equipos.Equipo;
import ar.gov.justiciajujuy.sanpedro.inventario.equipos.EquipoRepository;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/admin/equipos/{equipoId}/auditoria")
public class MovimientoEquipoController {

    private final AuditoriaService auditoriaService;
    private final EquipoRepository equipoRepository;

    public MovimientoEquipoController(AuditoriaService auditoriaService, EquipoRepository equipoRepository) {
        this.auditoriaService = auditoriaService;
        this.equipoRepository = equipoRepository;
    }

    @GetMapping
    public String verHistorial(
            @PathVariable Long equipoId,
            @RequestParam(required = false) String usuario,
            @RequestParam(required = false) TipoMovimiento tipo,
            Model model) {
        Equipo equipo = equipoRepository.findById(equipoId).orElseThrow();
        model.addAttribute("equipo", equipo);
        model.addAttribute("historial", auditoriaService.obtenerHistorialFiltrado(equipoId, usuario, tipo));
        model.addAttribute("usuarioFiltro", usuario);
        model.addAttribute("tipoFiltro", tipo);
        model.addAttribute("tiposMovimiento", TipoMovimiento.values());
        return "admin/equipo-auditoria";
    }

    @PostMapping
    public String registrarMovimiento(@PathVariable Long equipoId,
                                      @RequestParam TipoMovimiento tipoMovimiento,
                                      @RequestParam(required = false) String usuarioDestino,
                                      @RequestParam(required = false) String ubicacionOrigen,
                                      @RequestParam(required = false) String ubicacionDestino,
                                      @RequestParam(required = false) String observaciones,
                                      Authentication authentication) {
        String admin = authentication != null ? authentication.getName() : "Sistema";
        auditoriaService.registrarMovimiento(equipoId, tipoMovimiento, usuarioDestino, ubicacionOrigen, ubicacionDestino, admin, observaciones);
        return "redirect:/admin/equipos/" + equipoId + "/auditoria?success=true";
    }

    @GetMapping("/{movId}/pdf")
    public ResponseEntity<byte[]> descargarPdf(@PathVariable Long equipoId, @PathVariable Long movId) {
        try {
            byte[] pdfBytes = auditoriaService.generarActaPdf(movId);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.setContentDispositionFormData("filename", "Acta_Movimiento_" + movId + ".pdf");
            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
