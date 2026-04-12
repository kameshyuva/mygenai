from functools import reduce
import operator
import json

# 1. Define the Map function
def map_parent_to_children(parent_node):
    # Extract parent details (everything except the nested list)
    parent_details = {k: v for k, v in parent_node.items() if k != "employees"}
    
    # Map over the children, merging parent details into each child
    # Using dictionary unpacking (**child, **parent_details)
    return list(map(lambda child: {**child, **parent_details}, parent_node["employees"]))

# 2. Execute the Map Phase
# This creates a list of lists: [[{emp1}, {emp2}], [{emp3}]]
mapped_data = map(map_parent_to_children, nested_json)

# 3. Execute the Reduce Phase
# This flattens the list of lists into a single list: [{emp1}, {emp2}, {emp3}]
flat_list = reduce(operator.concat, mapped_data, [])

# Print the result beautifully
print(json.dumps(flat_list, indent=4))
