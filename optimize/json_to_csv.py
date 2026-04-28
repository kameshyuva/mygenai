import csv
import io
from typing import Any, List, Dict

def flat_json_list_to_csv(data: List[Dict[str, Any]]) -> str:
    """
    Converts a list of flattened JSON dictionaries into a CSV string.
    Highly token-optimized for LLM context windows.
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

    # 2. Build the CSV in memory
    output = io.StringIO()
    
    # Using lineterminator='\n' instead of the default '\r\n' saves 
    # one hidden token per row in the context window.
    writer = csv.DictWriter(
        output, 
        fieldnames=headers, 
        lineterminator='\n',
        extrasaction='ignore' # Safely ignores keys that aren't in the header
    )
    
    writer.writeheader()
    for row in valid_rows:
        writer.writerow(row)
        
    # Return the string, stripping the final trailing newline to be perfectly lean
    return output.getvalue().strip()


# ==========================================
# Example usage block 
# ==========================================
if __name__ == "__main__":
    sample_flat_list = [
        {"alert_id": "A100", "severity": "High", "source": "Firewall"},
        {"alert_id": "A101", "severity": "Medium", "action_taken": "Blocked"}, 
        {"alert_id": "A102", "source": "Endpoint", "status": "Resolved"}
    ]
    
    print(flat_json_list_to_csv(sample_flat_list))
