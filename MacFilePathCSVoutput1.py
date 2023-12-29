import os
import csv

def index_files(folder_path, csv_output):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print("The provided folder path does not exist.")
        return
    
    # Get list of file names in the folder
    file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Write the file names to a CSV file
    with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['File Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for file_name in file_names:
            writer.writerow({'File Name': file_name})
            
    print(f"Index of files has been saved to {csv_output}")

# Example usage:

# folder_path = '/path/to/your/folder'
csv_output = 'output.csv'
index_files(folder_path, csv_output)
