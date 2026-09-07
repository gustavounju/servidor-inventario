package ar.gov.justiciajujuy.sanpedro.inventario.security;

public interface ModuloPermisoProjection {

	String getModuloCodigo();

	String getModuloNombre();

	String getModuloDescripcion();

	Integer getModuloOrden();

	String getPermisoCodigo();
}
