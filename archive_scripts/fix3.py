
f2 = r'g:\unju2025\google gravity\ServidorInventario\blueprints\bp_setup.py'
with open(f2, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'const cmd = "[Net.ServicePointManager]' in line and 'window.location.hostname' in line:
        # replace the whole line
        lines[i] = "                    const cmd = \"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex (New-Object System.Net.WebClient).DownloadString('http://\" + window.location.hostname + \":5000/script')\\\\n\";\n"
        print("Line replaced!")

with open(f2, 'w', encoding='utf-8') as f:
    f.writelines(lines)
