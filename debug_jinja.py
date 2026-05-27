
from jinja2 import Template

t = Template("{% if pc.ad_real_name %}{{ pc.ad_real_name }}{% else %}Missing{% endif %}")

# Case 1: Dict with key
print("Case 1:", t.render(pc={'ad_real_name': 'Gustavo'}))

# Case 2: Dict WITHOUT key
try:
    print("Case 2:", t.render(pc={'other_key': 'Value'}))
except Exception as e:
    print("Case 2 Failed:", e)
