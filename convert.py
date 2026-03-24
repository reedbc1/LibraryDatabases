import json
import csv

# Load the JSON data
with open('slcl_resources.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Open CSV file for writing
with open('slcl_resources.csv', 'w', newline='', encoding='utf-8') as csv_file:
    # Assuming all objects have the same keys, use the first object's keys as headers
    if data:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write each row
        for item in data:
            writer.writerow(item)