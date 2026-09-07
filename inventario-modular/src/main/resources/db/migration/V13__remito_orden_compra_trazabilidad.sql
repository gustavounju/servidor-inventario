ALTER TABLE stock_componentes
  ADD COLUMN remito VARCHAR(80) NULL AFTER capacidad,
  ADD COLUMN orden_compra VARCHAR(80) NULL AFTER remito,
  ADD COLUMN proveedor VARCHAR(120) NULL AFTER orden_compra;

ALTER TABLE componentes
  ADD COLUMN remito VARCHAR(80) NULL AFTER capacidad,
  ADD COLUMN orden_compra VARCHAR(80) NULL AFTER remito,
  ADD COLUMN proveedor VARCHAR(120) NULL AFTER orden_compra;
