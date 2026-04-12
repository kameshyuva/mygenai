import pandas as pd
import json

# 1. THE DATA: Contains missing keys, None values, empty lists, and empty dicts
messy_json = [
    {
        "dept": "Engineering",
        "info": {"floor": 5, "head": "Alice"},
        "employees": [
            {"id": 1, "name": "Bob", "metadata": {"status": "active"}},
            {"id": 2, "name": "Charlie", "metadata": {}} # Empty dict
        ]
    },
    {
        "dept": "Sales",
        "info": None, # None parent object
        "employees": [] # Empty list: This parent will be dropped by default
    },
    {
        "dept": "Marketing",
        "info": {"floor": 2, "head": None}, # None value in parent
        "employees": None # Null record_path: This would usually crash pandas
    },
    {
        "dept": "HR" # Missing 'info' and 'employees' keys entirely
    }
]

def robust_flatten(data, record_path, meta):
    """
    Flattens nested JSON while handling missing keys and null values.
    """
    # --- PRE-PROCESSING ---
    # Ensure the record_path exists and is a list for every item.
    # If it's None or missing, we set it to [] so json_normalize handles it safely.
    for item in data:
        if record_path not in item or not isinstance(item[record_path], list):
            item[record_path] = []

    # --- NORMALIZATION ---
    # errors='ignore' ensures it doesn't crash if meta keys are missing
    df = pd.json_normalize(
        data,
        record_path=record_path,
        meta=meta,
        errors='ignore'
    )

    # --- POST-PROCESSING ---
    if not df.empty:
        # Replace pandas 'NaN' with Python 'None' or an empty string for clean JSON
        # This fixes issues where 'None' in JSON became 'NaN' in Pandas
        df = df.replace({pd.NA: None, float('nan'): None})
        
        # Optional: Standardize nested columns that might have remained as NaN
        # (e.g., if 'metadata' was missing in some records)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x if x is not None else "")

    return df

# Define what we want to extract
# We use a list for nested meta keys (e.g., info -> head)
target_record = "employees"
target_meta = ["dept", ["info", "floor"], ["info", "head"]]

# Execute
df_flat = robust_flatten(messy_json, target_record, target_meta)

# Output Results
print("--- Resulting DataFrame ---")
print(df_flat.to_string())

print("\n--- Final Cleaned JSON ---")
final_json = df_flat.to_dict(orient="records")
print(json.dumps(final_json, indent=4))
