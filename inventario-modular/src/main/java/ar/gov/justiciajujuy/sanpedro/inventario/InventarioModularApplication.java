package ar.gov.justiciajujuy.sanpedro.inventario;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class InventarioModularApplication {

	public static void main(String[] args) {
		SpringApplication.run(InventarioModularApplication.class, args);
	}

}
