package ar.gob.justicia.sanpedro.inventario.login;

record AuthenticationResult(boolean success, AuthenticatedUser user, String message) {

	static AuthenticationResult success(AuthenticatedUser user) {
		return new AuthenticationResult(true, user, "");
	}

	static AuthenticationResult failure(String message) {
		return new AuthenticationResult(false, null, message);
	}
}
