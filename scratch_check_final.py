import os

file_path = "inventario.ps1"
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    stack = []
    in_string = False
    string_marker = None
    in_comment = False
    
    for i, char in enumerate(content):
        # Handle comments
        if not in_string and char == "#":
            in_comment = True
        if in_comment and char == "\n":
            in_comment = False
            
        if in_comment:
            continue
            
        # Handle strings
        if char == '"' or char == "'":
            if not in_string:
                in_string = True
                string_marker = char
            elif string_marker == char:
                # Check for escaped quotes (double quotes in PS)
                if i + 1 < len(content) and content[i+1] == char:
                    # Skip next quote
                    pass 
                else:
                    in_string = False
                    string_marker = None
        
        if not in_string:
            if char == "{":
                # Find line number
                line_num = content[:i].count("\n") + 1
                stack.append(line_num)
            elif char == "}":
                line_num = content[:i].count("\n") + 1
                if stack:
                    stack.pop()
                else:
                    print(f"ERROR: Extra '}}' on line {line_num}")
    
    if stack:
        for s in stack:
            print(f"ERROR: Unclosed '{{' starting on line {s}")
    else:
        print("SUCCESS: All braces balanced (strings ignored).")
else:
    print("File not found.")
