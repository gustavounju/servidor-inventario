import os

file_path = "inventario.ps1"
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    opens = 0
    closes = 0
    in_comment = False
    
    # Very simple brace counter (ignores strings/comments)
    for i, char in enumerate(content):
        if char == "{":
            opens += 1
        elif char == "}":
            closes += 1
            
    print(f"Total Opening Braces {{ : {opens}")
    print(f"Total Closing Braces }} : {closes}")
    if opens > closes:
        print(f"Missing {opens - closes} closing braces.")
    elif closes > opens:
        print(f"Extra {closes - opens} closing braces.")
    else:
        print("Braces are balanced.")
else:
    print("File not found.")
