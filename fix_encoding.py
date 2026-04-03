import os

files_to_fix = [
    'src/agents/rewriter.py',
    'src/workflow.py',
    'src/agents/reranker.py',
    'src/agents/generator.py'
]

for file_path in files_to_fix:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}, does not exist.")
        continue
        
    try:
        # Try to read with various encodings to find the right one
        content = None
        for enc in ['utf-8-sig', 'utf-16', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                content = data.decode(enc)
                print(f"Read {file_path} using {enc}")
                break
            except Exception:
                continue
        
        if content:
            # Write back as clean UTF-8 (without BOM)
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print(f"Successfully normalized {file_path} to UTF-8")
        else:
            print(f"Could not decode {file_path}")
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
