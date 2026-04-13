with open('templates/fueros.html', 'r', encoding='utf-8') as f:
    content = f.read()

header_old = '<h6 class="fw-bold mb-0 text-dark"><i class="bi bi-printer-fill text-secondary me-2"></i>Impresoras ({{ printers|length }})</h6>'
header_new = '''{% set own_printers = printers | selectattr('physical_fuero', 'equalto', fuero_param) | list if fuero_param else printers %}
                <h6 class="fw-bold mb-0 text-dark">
                    <i class="bi bi-printer-fill text-secondary me-2"></i>
                    {% if fuero_param %}
                        Impresoras propias ({{ own_printers|length }}) <span class="text-muted small fw-normal ms-1">/ Ext. ({{ printers|length - own_printers|length }})</span>
                    {% else %}
                        Impresoras huérfanas ({{ printers|length }})
                    {% endif %}
                </h6>'''

content = content.replace(header_old, header_new)

td_old = '''<td class="small">
                                    {{ prnt.brand_model or 'No especificado' }}
                                </td>'''

td_new = '''<td class="small">
                                    {{ prnt.brand_model or 'No especificado' }}
                                    {% if fuero_param and prnt.physical_fuero and prnt.physical_fuero != fuero_param %}
                                    <div class="mt-1">
                                        <span class="badge bg-warning text-dark border border-warning" style="font-size: 0.70rem;">
                                            <i class="bi bi-geo-alt-fill me-1"></i> Físicamente en: {{ prnt.physical_fuero }}
                                        </span>
                                    </div>
                                    {% endif %}
                                </td>'''

content = content.replace(td_old, td_new)

with open('templates/fueros.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
