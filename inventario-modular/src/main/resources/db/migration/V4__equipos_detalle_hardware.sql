ALTER TABLE equipos
  ADD COLUMN ram_detalles VARCHAR(500) NULL AFTER ram_mb,
  ADD COLUMN ram_seriales VARCHAR(500) NULL AFTER ram_detalles,
  ADD COLUMN discos_modelos VARCHAR(500) NULL AFTER ram_seriales,
  ADD COLUMN discos_seriales VARCHAR(500) NULL AFTER discos_modelos,
  ADD COLUMN motherboard_modelo VARCHAR(255) NULL AFTER discos_seriales,
  ADD COLUMN motherboard_serial VARCHAR(255) NULL AFTER motherboard_modelo,
  ADD COLUMN monitores VARCHAR(500) NULL AFTER motherboard_serial,
  ADD COLUMN teclado VARCHAR(180) NULL AFTER monitores,
  ADD COLUMN mouse VARCHAR(180) NULL AFTER teclado;
