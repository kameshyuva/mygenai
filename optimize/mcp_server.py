import json
from mcp.server.fastmcp import FastMCP
from json_to_md_table import convert_to_md

mcp = FastMCP("DataComparisonServer")

# Global in-memory cache for the flattened data
FLATTENED_DB = []

def initialize_data(file_path: str):
    """Flatten complex nested JSON into a simple list of enriched records."""
    global FLATTENED_DB
    with open(file_path, "r") as f:
        raw = json.load(f)
    
    # Tailor this loop to your 'Complex object' structure
    # Assumption: {'parents': [{'metadata': {...}, 'children': [...]}]}
    temp_list = []
    for parent in raw.get("parents", []):
        p_meta = parent.get("metadata", {})
        for child in parent.get("children", []):
            # Inject parent info into every child for self-contained context
            flat_record = {
                "parent_id": p_meta.get("id"),
                "parent_cat": p_meta.get("category"),
                **child # Spread child details
            }
            temp_list.append(flat_record)
    FLATTENED_DB = temp_list

@mcp.tool()
async def get_comparison_batch(offset: int = 0, limit: int = 5) -> str:
    """
    Fetches a flattened batch of child records in Markdown format.
    Use this to compare multiple children. Check 'next_offset' to continue.
    """
    batch = FLATTENED_DB[offset : offset + limit]
    has_more = (offset + limit) < len(FLATTENED_DB)
    
    md_table = convert_to_md(batch)
    
    return json.dumps({
        "comparison_table": md_table,
        "next_offset": offset + limit if has_more else None,
        "total_records": len(FLATTENED_DB),
        "note": "Examine the table above and summarize key findings before moving to next_offset."
    }, separators=(',', ':'))

if __name__ == "__main__":
    initialize_data("large_nested_data.json")
    mcp.run()
