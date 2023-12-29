import os
import json

def index_files(folder_path, json_output):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print("The provided folder path does not exist.")
        return
    
    # Get list of file names in the folder
    file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Write the file names to a JSON file
    with open(json_output, 'w', encoding='utf-8') as jsonfile:
        json.dump(file_names, jsonfile, ensure_ascii=False, indent=4)
            
    print(f"Index of files has been saved to {json_output}")

# Example usage:

# folder_path = '/path/to/your/folder'
json_output = 'output-01.json'
index_files(folder_path, json_output)
