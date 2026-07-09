import re

def main():
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        idx_content = f.read()

    # 1. Remove CSS
    css_pattern = re.compile(r'(\s*\.rack-grid\s*\{.*?\s*\.rack-info\s*p\s*\{[^}]*\}\n)', re.DOTALL)
    idx_content = css_pattern.sub('', idx_content)

    # 2. Remove HTML
    switch_html_pattern = re.compile(r'(\s*<div id="switchStatusContainer".*?</div>\s*</div>)', re.DOTALL)
    idx_content = switch_html_pattern.sub('', idx_content)

    # 3. Remove JS
    js_pattern = re.compile(r'(\s*<script>\s*document\.addEventListener\(\'DOMContentLoaded\', \(\) => \{\s*refreshSwitchStatus\(\);\s*\}\);\s*async function refreshSwitchStatus\(\).*?\}\s*\} catch\(e\) \{ console\.error\(e\); \}\s*\}\s*</script>\s*)', re.DOTALL)
    idx_content = js_pattern.sub('\n', idx_content)

    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(idx_content)

if __name__ == '__main__':
    main()
