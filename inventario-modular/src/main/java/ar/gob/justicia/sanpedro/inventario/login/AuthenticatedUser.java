package ar.gob.justicia.sanpedro.inventario.login;

import java.io.Serializable;

public record AuthenticatedUser(String username, String displayName, String role, boolean superuser) implements Serializable {
}
