import os

file_path = 'src/agents/generator.py'
with open(file_path, 'rb') as f:
    data = f.read()

# Triple quote in Python
pattern = b'\"\"\"'
start = data.find(pattern)

if start != -1:
    with open(file_path, 'wb') as f:
        f.write(data[start:])
    print(f"Force fixed {file_path}. Data now starts with triple-quote.")
else:
    print(f"Triple-quote not found in {file_path} binary data.")
    # Fallback to 'import'
    start = data.find(b'import')
    if start != -1:
        with open(file_path, 'wb') as f:
            f.write(data[start:])
        print(f"Force fixed {file_path} (using 'import').")
    else:
        print("Could not find any code start patterns.")
