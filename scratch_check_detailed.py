import os

file_path = "inventario.ps1"
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    stack = []
    for i, line in enumerate(lines, 1):
        # Remove comments for brace counting
        clean_line = line.split("#")[0]
        
        for char in clean_line:
            if char == "{":
                stack.append(i)
            elif char == "}":
                if stack:
                    stack.pop()
                else:
                    print(f"ERROR: Extra '}}' on line {i}")
        
        if "try" in clean_line.lower():
            # Check if this line or next lines have a catch
            found_catch = False
            for j in range(i, min(i+100, len(lines))):
                if "catch" in lines[j].lower():
                    found_catch = True
                    break
            if not found_catch:
                 print(f"WARNING: 'try' on line {i} might be missing a 'catch' in the next 100 lines.")

    if stack:
        for s in stack:
            print(f"ERROR: Unclosed '{{' starting on line {s}")
else:
    print("File not found.")
