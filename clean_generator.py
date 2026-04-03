import os

file_path = 'src/agents/generator.py'
if os.path.exists(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Aggressively find the first character that belongs to legitimate code
    # (starts with " or ' or # or import or from or line 1 comment)
    # Most likely the first byte is 0xBB (part of corrupted BOM).
    
    # Strip any non-ASCII leading bytes that are obviously not code start
    start_index = 0
    while start_index < len(data) and data[start_index] > 127:
        start_index += 1
        
    clean_data = data[start_index:]
    
    try:
        content = clean_data.decode('utf-8')
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print(f"Cleaned {file_path}. Removed {start_index} leading bytes.")
    except Exception as e:
        print(f"Failed to decode cleaned data: {e}")
else:
    print(f"{file_path} not found.")
