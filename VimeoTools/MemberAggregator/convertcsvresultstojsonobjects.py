import csv
import json
import os
from decimal import Decimal

# Function to parse CSV and create data objects
def parse_vimeo_csv(file_path):
    data = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Convert necessary fields and handle array data
            data_object = {
                'name': row['name'],
                'description': row['description'],
                'link': row['link'],
                'duration': int(row['duration']) if row['duration'] else 0,
                'date': row['upload_date'],
                'download': row['download'].lower() == 'true',
                'files': eval(row['files']) if row['files'] else [],  # Convert stringified list to actual list
                'transcript': row['transcript']  # assuming transcript field is directly usable
            }
            
            # Append the formatted data object to the list
            data.append(data_object)
    
    return data

# Function to save JSON file with _CleanedJSON appended to the filename
def save_to_json(data, file_path):
    # Get directory, filename, and extension
    directory = os.path.dirname(file_path)
    filename = os.path.splitext(os.path.basename(file_path))[0]
    new_file_path = os.path.join(directory, f"{filename}_CleanedJSON.json")
    
    # Write data to JSON file
    with open(new_file_path, mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)
    print(f"Data saved to {new_file_path}")

# Path to your CSV file
file_path = './vimeo_videos_2024-10-31_00-54-11.csv'
# Process CSV data and save as JSON
vimeo_data = parse_vimeo_csv(file_path)
save_to_json(vimeo_data, file_path)
