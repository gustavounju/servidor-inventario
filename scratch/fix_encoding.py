
filepath = 'blueprints/bp_tasks.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix mangled UTF-8 characters and double escapes
text = text.replace('ðŸ“ž', '📞')
text = text.replace('TelÃ©fono', 'Teléfono')
text = text.replace('ðŸ“…', '📅')
text = text.replace('ðŸ–¥ï¸', '🖥️')
text = text.replace('ðŸ‘¤', '👤')
text = text.replace('ðŸ·ï¸', '🏷️')
text = text.replace('ðŸ“', '📝')
text = text.replace('ðŸš¨', '🚨')
text = text.replace('ðŸ§–', '👨‍🔧')
text = text.replace('ðŸ⚖ï¸', '⚖️')
text = text.replace('Ã¡', 'á')
text = text.replace('Ã©', 'é')
text = text.replace('Ã\xad', 'í')
text = text.replace('Ã³', 'ó')
text = text.replace('Ãº', 'ú')
text = text.replace('Ã±', 'ñ')

# Fix double escaped newlines
text = text.replace('\\\\n', '\\n')

with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print("Emojis and newlines fixed")
