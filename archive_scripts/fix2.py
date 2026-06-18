
f2 = r'g:\unju2025\google gravity\ServidorInventario\blueprints\bp_setup.py'
with open(f2, 'r', encoding='utf-8') as f:
    text2 = f.read()

bad = "5000/script')\n\";"
good = "5000/script')\\n\";"

if bad in text2:
    print("Encontrado bad en bp_setup.py")
    text2 = text2.replace(bad, good)
    with open(f2, 'w', encoding='utf-8') as f:
        f.write(text2)
else:
    print("NO ENCONTRADO EN bp_setup.py")
