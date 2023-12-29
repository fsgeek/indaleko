import os
import json
import datetime

def get_file_metadata(file_path):
    """
    Get metadata for a file.
    """
    try:
        # Get file statistics
        stats = os.stat(file_path)
        
        # Convert timestamps to readable format
        created_time = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Construct metadata dictionary
        metadata = {
            'size': stats.st_size,
            'created': created_time,
            'modified': modified_time,
        }
        
        return metadata
    except Exception as e:
        print(f"Could not get metadata for file: {file_path}. Error: {str(e)}")
        return {}

def index_files(folder_path, json_output):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print("The provided folder path does not exist.")
        return
    
    # Get list of file names and their metadata in the folder
    files_metadata = []
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            metadata = get_file_metadata(file_path)
            metadata['name'] = file_name
            files_metadata.append(metadata)
    
    # Write the file names and metadata to a JSON file
    with open(json_output, 'w', encoding='utf-8') as jsonfile:
        json.dump(files_metadata, jsonfile, ensure_ascii=False, indent=4)
            
    print(f"Index of files and their metadata has been saved to {json_output}")

# Example usage:

# folder_path = '/path/to/your/folder'
json_output = 'output_w_meta.json'
index_files(folder_path, json_output)
