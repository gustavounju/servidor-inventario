import re

with open('blueprints/bp_tasks.py', 'r', encoding='utf-8') as f:
    c = f.read()

match = re.search(r'@bp_tasks\.route\([\'"]/api/visor', c)
if match:
    start = match.start()
    print(c[start:start+1500])
else:
    print('Not found')
