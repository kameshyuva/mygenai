import json

def json_to_md_table(json_data, empty_placeholder="-"):
    # If the JSON is a single dictionary, wrap it in a list
    if isinstance(json_data, dict):
        json_data = [json_data]
        
    if not json_data:
        return "No data provided."

    # Extract all unique headers across all dictionaries
    headers = []
    for item in json_data:
        for key in item.keys():
            if key not in headers:
                headers.append(key)

    md_lines = []
    
    # 1. Build Header Row
    md_lines.append("| " + " | ".join(headers) + " |")
    
    # 2. Build Separator Row
    md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # 3. Build Data Rows
    for item in json_data:
        row = []
        for header in headers:
            val = item.get(header)
            
            # --- HANDLE EMPTY OR NULL FIELDS HERE ---
            if val is None or val == "" or val == [] or val == {}:
                row.append(empty_placeholder)
            else:
                # Convert to string, escape pipes to avoid breaking the table, and remove newlines
                clean_val = str(val).replace("|", "\\|").replace("\n", " ")
                row.append(clean_val)
                
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)

# --- EXAMPLE USAGE ---
json_string = '''
[
    {"name": "Alice", "role": "Admin", "department": "IT"},
    {"name": "Bob", "role": null, "department": ""},
    {"name": "Charlie", "department": "HR", "notes": []}
]
'''
data = json.loads(json_string)
print(json_to_md_table(data, empty_placeholder="*N/A*"))
