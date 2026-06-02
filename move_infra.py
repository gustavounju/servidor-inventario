import re

# 1. Read visor_tareas.html
with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
    visor_content = f.read()

# 2. Extract and remove CSS
css_pattern = re.compile(r'(\s*\.rack-grid\s*\{.*?\s*\.rack-info\s*p\s*\{[^}]*\}\n)', re.DOTALL)
match_css = css_pattern.search(visor_content)
css_block = match_css.group(1) if match_css else ""
visor_content = css_pattern.sub('', visor_content)

# 3. Extract and remove HTML Containers
html_pattern = re.compile(r'(\s*<div id="rackStatusContainer".*?<div id="switchStatusContainer".*?</div>\s*</div>\s*)<div class="section-header">', re.DOTALL)
match_html = html_pattern.search(visor_content)
html_block = match_html.group(1) if match_html else ""
visor_content = html_pattern.sub('\n            <div class="section-header">', visor_content)

# 4. Extract and remove JS refresh methods
js_pattern = re.compile(r'(\s*// Initialize rack status on load.*?\}\s*)function applyFilters\(\)', re.DOTALL)
match_js = js_pattern.search(visor_content)
js_block = match_js.group(1) if match_js else ""
visor_content = js_pattern.sub('\n        function applyFilters()', visor_content)

# Remove `refreshRackStatus(); refreshSwitchStatus();` from refreshData()
visor_content = visor_content.replace('            // Also refresh rack and switch status\n            refreshRackStatus();\n            refreshSwitchStatus();\n', '')

# 5. Extract and remove Modal JS & HTML
modal_pattern = re.compile(r'(\s*// --- Rack Audit Details Modal ---.*?)</body>', re.DOTALL)
match_modal = modal_pattern.search(visor_content)
modal_block = match_modal.group(1) if match_modal else ""
visor_content = modal_pattern.sub('\n</body>', visor_content)

# Save visor_tareas.html
with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
    f.write(visor_content)

# 6. Inject into index.html
with open('templates/index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# Inject CSS
index_content = index_content.replace('</style>', f'{css_block}</style>')

# Inject HTML
# Let's put it right before `{% block dashboard_content %}`
index_content = index_content.replace('{% block dashboard_content %}', f'{html_block}\n        {{% block dashboard_content %}}')

# Inject JS and Modal at the end of the file, before </body>
# But the modal_block contains `</script>\n\n    <!-- Modal Detalle Rack -->...`
# So we can just put it right before </body>. Wait, `modal_block` has `</script>` at the end of the JS part.
# Let's clean up modal_block so it fits well.
# It starts with `// --- Rack Audit Details Modal` inside a <script>, then closes </script>, then the HTML modal.
# We also have `js_block` which is just JS functions.
# Let's inject them at the bottom of index.html, right before </body>.
script_injection = f"""
    <script>
{js_block}
{modal_block}
"""
index_content = index_content.replace('</body>', f'{script_injection}\n</body>')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(index_content)

print("Migration successful.")
