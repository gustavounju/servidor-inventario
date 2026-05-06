content = open('services/dashboard_overview.py', 'r', encoding='utf-8').read()

# Replace for filter_sql (p. prefix)
content = content.replace(
    "AND p.alerta_sin_impresora = 0",
    "AND IF(p.alerta_sin_impresora = 1 AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) = 0"
)
content = content.replace(
    "(p.alerta_ram_baja + p.alerta_sin_impresora + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado)",
    "(p.alerta_ram_baja + IF(p.alerta_sin_impresora = 1 AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado)"
)

# Replace for KPIs (no prefix)
content = content.replace(
    "AND alerta_sin_impresora = 0",
    "AND IF(alerta_sin_impresora = 1 AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) = 0"
)
content = content.replace(
    "(alerta_ram_baja + alerta_sin_impresora + alerta_disco + alerta_uptime + alerta_nombre_duplicado)",
    "(alerta_ram_baja + IF(alerta_sin_impresora = 1 AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + alerta_disco + alerta_uptime + alerta_nombre_duplicado)"
)

with open('services/dashboard_overview.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced!")
