import pandas as pd
import json

nested_json = [
    {
        "department": "Engineering",
        "head": "Alice",
        "employees": [
            {"id": 1, "name": "Bob", "role": "Backend"},
            {"id": 2, "name": "Charlie", "role": "Frontend"}
        ]
    },
    {
        "department": "Sales",
        "head": "David",
        "employees": [
            {"id": 3, "name": "Eve", "role": "Executive"}
        ]
    }
]

# Flatten the JSON
df = pd.json_normalize(
    nested_json, 
    record_path='employees',     # The nested list to unpack
    meta=['department', 'head']  # Parent details to attach to each record
)

print("--- DataFrame Output ---")
print(df)

# If you need it back as a list of JSON-like dictionaries:
flat_list = df.to_dict(orient='records')

print("\n--- Back to JSON Output ---")
print(json.dumps(flat_list, indent=4))
