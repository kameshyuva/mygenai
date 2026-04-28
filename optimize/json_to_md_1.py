from typing import Any, List, Dict

def flat_json_list_to_markdown_table(data: List[Dict[str, Any]]) -> str:
    """
    Iteratively converts a list of flattened JSON dictionaries into a Markdown table.
    Dynamically extracts headers to handle inconsistent keys across rows.
    """
    # 1. Validate the input
    if not data or not isinstance(data, list):
        return "No data returned."
        
    valid_rows = [row for row in data if isinstance(row, dict)]
    if not valid_rows:
        return "No valid tabular data found."

    # 2. Extract all unique headers while preserving appearance order
    headers = []
    seen_headers = set()
    for row in valid_rows:
        for key in row.keys():
            if key not in seen_headers:
                headers.append(key)
                seen_headers.add(key)
                
    if not headers:
        return "Empty data objects."

    table_lines = []
    
    # 3. Build the Header Row and Separator
    header_row = "| " + " | ".join(f"`{h}`" for h in headers) + " |"
    table_lines.append(header_row)
    
    separator_row = "|" + "|".join("---" for _ in headers) + "|"
    table_lines.append(separator_row)
    
    # 4. Build the Data Rows iteratively
    for row in valid_rows:
        row_values = []
        for header in headers:
            # Use .get() to handle cases where a row might be missing a column key
            val = row.get(header, "")
            
            # Sanitize the value to prevent Markdown table formatting from breaking
            safe_val = str(val).replace("|", "\\|").replace("\n", " ")
            row_values.append(safe_val)
            
        data_row = "| " + " | ".join(row_values) + " |"
        table_lines.append(data_row)
        
    return "\n".join(table_lines)


# ==========================================
# Example usage block 
# ==========================================
if __name__ == "__main__":
    sample_flat_list = [
        {"alert_id": "A100", "severity": "High", "source": "Firewall"},
        {"alert_id": "A101", "severity": "Medium", "action_taken": "Blocked"}, # Notice different keys
        {"alert_id": "A102", "source": "Endpoint", "status": "Resolved"}
    ]
    
    print(flat_json_list_to_markdown_table(sample_flat_list))
