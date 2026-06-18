import os

file_path = "inventario.ps1"
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    stack = []
    for line_num, line in enumerate(lines, 1):
        for char in line:
            if char == "{":
                stack.append(line_num)
            elif char == "}":
                if stack:
                    stack.pop()
                else:
                    print(f"ERROR: Extra '}}' on line {line_num}")
    
    if stack:
        for s in stack:
            print(f"ERROR: Unclosed '{{' starting on line {s}")
else:
    print("File not found.")
