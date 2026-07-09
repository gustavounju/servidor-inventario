import re

def main():
    # 1. READ FILES
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        idx_content = f.read()
    with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
        visor_content = f.read()

    # 2. EXTRACT SWITCHES CSS FROM visor_tareas
    css_pattern = re.compile(r'(\s*\.rack-grid\s*\{.*?\s*\.rack-info\s*p\s*\{[^}]*\}\n)', re.DOTALL)
    match_css = css_pattern.search(visor_content)
    css_block = match_css.group(1) if match_css else ""

    # 3. EXTRACT SWITCHES HTML FROM visor_tareas
    switch_html_pattern = re.compile(r'(\s*<div id="switchStatusContainer".*?</div>\s*</div>)', re.DOTALL)
    match_switch_html = switch_html_pattern.search(visor_content)
    switch_html = match_switch_html.group(1) if match_switch_html else ""
    
    # Remove from visor_tareas
    if switch_html:
        visor_content = visor_content.replace(switch_html, '')

    # 4. EXTRACT SWITCHES JS FROM visor_tareas
    switch_js_pattern = re.compile(r'(\s*async function refreshSwitchStatus\(\).*?\}\s*\} catch\(e\) \{ console\.error\(e\); \}\s*\})', re.DOTALL)
    match_switch_js = switch_js_pattern.search(visor_content)
    switch_js = match_switch_js.group(1) if match_switch_js else ""
    
    # Remove from visor_tareas
    if switch_js:
        visor_content = visor_content.replace(switch_js, '')

    # Remove refreshSwitchStatus(); from DOMContentLoaded in visor_tareas
    visor_content = visor_content.replace('            refreshSwitchStatus();\n', '')
    # Remove from refreshData
    visor_content = visor_content.replace('            refreshSwitchStatus();\n', '')

    # 5. INJECT BLOCKS INTO index.html
    # Inject CSS
    if css_block and css_block not in idx_content:
        idx_content = idx_content.replace('</style>', f'{css_block}\n    </style>')

    # Inject HTML
    if switch_html and switch_html not in idx_content:
        idx_content = idx_content.replace('{% block dashboard_content %}', f'{switch_html}\n\n        {{% block dashboard_content %}}')

    # Inject JS
    if switch_js and switch_js not in idx_content:
        script_injection = f"""
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            refreshSwitchStatus();
        }});
{switch_js}
    </script>
"""
        idx_content = idx_content.replace('</body>', f'{script_injection}\n</body>')

    # 6. SAVE FILES
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(idx_content)
    with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
        f.write(visor_content)

    print("Migration of Switches successful.")

if __name__ == '__main__':
    main()
