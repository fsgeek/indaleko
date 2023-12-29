import json

def count_items_in_json(file_path):
    try:
        # Open the JSON file for reading
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            # Load the data from the JSON file
            data = json.load(jsonfile)

        # Check if data is a list and then count the number of items
        if isinstance(data, list):
            return len(data)
        else:
            return "The file does not contain a list."
    except FileNotFoundError:
        return "File not found."
    except json.JSONDecodeError:
        return "Error decoding JSON."

# Replace with your actual JSON file path to the actual file name NOT to a folder.
json_output = '/Users/.../'  # Ensure this is a file path to a file not a folder. Make a name...I am withopen() in write mode so the file will becreated if there isn't already a file.

# Count the items and print the result
item_count = count_items_in_json(json_output)
print(f"Number of items in the JSON file: {item_count}")
