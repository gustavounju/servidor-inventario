package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.util.Locale;

public enum OrigenIdentidad {
	AD,
	LOCAL;

	public static OrigenIdentidad desde(String valor) {
		if (valor == null || valor.isBlank()) {
			return AD;
		}
		return OrigenIdentidad.valueOf(valor.trim().toUpperCase(Locale.ROOT));
	}
}
