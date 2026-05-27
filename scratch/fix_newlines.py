import os

filepath = 'blueprints/bp_tasks.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter out empty lines that were added
new_lines = []
for line in lines:
    if line.strip() == '':
        # Only keep if the previous line wasn't empty or if it's a real empty line
        # Actually, let's just remove all extra newlines and keep only those that were originally there.
        # This is hard.
        pass

# Better: just replace \n\n with \n if the file was doubled
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# If it's CRLF converted to LF with extra breaks:
text = text.replace('\n\n', '\n')

with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print("File newlines fixed")
