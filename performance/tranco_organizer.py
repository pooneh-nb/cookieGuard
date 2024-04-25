from pathlib import Path
import csv

tranco_path = Path(Path.home(), 'cookieProtect/performance/tranco_XJ4JN.csv')

# Open the file in read mode
with open(tranco_path, mode='r', newline='', encoding='utf-8') as file:
    # Create a CSV reader
    reader = csv.reader(file)
    sites = []
    # Process each row
    for row in reader:
        sites.append([row[1]])


tranco_list_path =  Path(Path.home(), 'cookieProtect/performance/tranco.csv')
with open(tranco_list_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Write all the data rows
    writer.writerows(sites)