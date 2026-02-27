import os

f1 = r'g:\unju2025\google gravity\ServidorInventario\templates\index.html'
f2 = r'g:\unju2025\google gravity\ServidorInventario\blueprints\bp_setup.py'

with open(f1, 'r', encoding='utf-8') as f:
    text = f.read()
# The literal newline has to be turned into a backslash and an n
bad_snippet1 = "5000/script')\n\";"
good_snippet1 = "5000/script')\\n\";"
text = text.replace(bad_snippet1, good_snippet1)
bad_snippet2 = "5000/script')\r\n\";"
text = text.replace(bad_snippet2, good_snippet1)

with open(f1, 'w', encoding='utf-8') as f:
    f.write(text)

with open(f2, 'r', encoding='utf-8') as f:
    text2 = f.read()

text2 = text2.replace(bad_snippet1, good_snippet1).replace(bad_snippet2, good_snippet1)

with open(f2, 'w', encoding='utf-8') as f:
    f.write(text2)

print("¡Archivos corregidos!")
