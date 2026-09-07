package ar.gov.justiciajujuy.sanpedro.inventario.web;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ScriptIntegrityController {

	private static final String SCRIPT_PATH = "static/scripts/windows/inventario-modular.ps1";

	@GetMapping(value = "/scripts/windows/inventario-modular.ps1.sha256", produces = MediaType.TEXT_PLAIN_VALUE)
	public String inventarioWindowsSha256() throws IOException, NoSuchAlgorithmException {
		/*
		 * El hash se calcula al servirlo para evitar que el comando del login quede
		 * desincronizado cuando el script cambie en una release futura.
		 */
		byte[] scriptBytes = new ClassPathResource(SCRIPT_PATH).getInputStream().readAllBytes();
		byte[] hash = MessageDigest.getInstance("SHA-256").digest(scriptBytes);
		return HexFormat.of().formatHex(hash) + System.lineSeparator();
	}
}
