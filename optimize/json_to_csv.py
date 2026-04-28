import csv
import io
from typing import Any, List, Dict

def flat_json_list_to_csv(data: List[Dict[str, Any]], empty_filler: str = "-") -> str:
    """
    Converts a list of flattened JSON dictionaries into a CSV string.
    Explicitly handles empty, None, or missing fields to prevent LLM column drift.
    """
    if not data or not isinstance(data, list):
        return "No data returned."
        
    valid_rows = [row for row in data if isinstance(row, dict)]
    if not valid_rows:
        return "No valid tabular data found."

    # 1. Extract all unique headers dynamically
    headers = []
    seen_headers = set()
    for row in valid_rows:
        for key in row.keys():
            if key not in seen_headers:
                headers.append(key)
                seen_headers.add(key)
                
    if not headers:
        return "Empty data objects."

    output = io.StringIO()
    
    # 2. Configure DictWriter
    writer = csv.DictWriter(
        output, 
        fieldnames=headers, 
        lineterminator='\n',
        extrasaction='ignore' 
    )
    
    writer.writeheader()
    
    # 3. Process rows and fill empty fields
    for row in valid_rows:
        safe_row = {}
        for header in headers:
            val = row.get(header)
            
            # Catch missing keys, None values, and empty strings/lists
            if val is None or val == "" or val == []:
                safe_row[header] = empty_filler
            else:
                # Optional: Strip newline characters from strings to ensure they 
                # don't break the CSV row structure
                if isinstance(val, str):
                    safe_row[header] = val.replace("\n", " ").strip()
                else:
                    safe_row[header] = val
                    
        writer.writerow(safe_row)
        
    return output.getvalue().strip()


# ==========================================
# Example usage block 
# ==========================================
if __name__ == "__main__":
    sample_flat_list = [
        {"alert_id": "A100", "severity": "High", "source": "Firewall", "status": None},
        {"alert_id": "A101", "severity": "Medium", "action_taken": "Blocked"}, 
        {"alert_id": "A102", "source": "Endpoint", "status": "", "notes": []}
    ]
    
    print(flat_json_list_to_csv(sample_flat_list))
