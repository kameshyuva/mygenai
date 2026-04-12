def flatten_nested(data, children_key="children", parent_context=None):
    if parent_context is None:
        parent_context = {}

    for item in data:
        # Separate the current level's metadata from its children
        current_details = {k: v for k, v in item.items() if k != children_key}
        
        # Combine inherited parent context with current details
        combined_context = {**parent_context, **current_details}
        
        if children_key in item and isinstance(item[children_key], list):
            # Recurse deeper, passing down the accumulated context
            yield from flatten_nested(item[children_key], children_key, combined_context)
        else:
            # We hit a leaf node (the individual item), yield it with all parent data
            yield combined_context

# Usage:
# flat_list = list(flatten_nested(deeply_nested_json, children_key="employees"))
