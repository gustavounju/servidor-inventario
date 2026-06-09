import re

with open('templates/visor_tareas.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the jinja block for ad-match in tareas_hoy (lines 444-467 approx)
content = re.sub(r'{%\s*if task\.has_user_match\s*%}.*?{%\s*endif\s*%}', '', content, flags=re.DOTALL)

# Remove the jinja block for ad-match in tareas_anteriores (lines 513-529 approx)
content = re.sub(r'{%\s*if task\.has_user_match\s*%}.*?{%\s*endif\s*%}', '', content, flags=re.DOTALL)

# Remove the renderAdMatch function definition
content = re.sub(r'function renderAdMatch\(task\) \{.*?\n        \}', '', content, flags=re.DOTALL)

# Remove the call to renderAdMatch(task) in JS renderHoy
content = re.sub(r'\$\{renderAdMatch\(task\)\}', '', content)

# Remove the call to renderAdMatch(task) in JS renderAnteriores
content = re.sub(r'\$\{renderAdMatch\(task\)\}', '', content)

# Remove ad-match CSS
content = re.sub(r'\.ad-match-box.*?\.ad-match-note\s*\{.*?\}', '', content, flags=re.DOTALL)
# One more pass to get any leftover ad-match CSS
content = re.sub(r'\.ad-match-[^{]*\{[^}]*\}', '', content, flags=re.DOTALL)

with open('templates/visor_tareas.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Visor tareas limpiado con éxito.")
