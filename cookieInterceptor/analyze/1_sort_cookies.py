import os
import json
import utilities
from pathlib import Path

crawls_path = Path('server/output')

sites_dirs = utilities.get_directories_in_a_directory(crawls_path)

for site_dir in sites_dirs:
    data = []
    sorted_cookies_dir = Path('analyze/data/sorted_cookies')
    if not os.path.exists(sorted_cookies_dir):
        os.mkdir(sorted_cookies_dir)
    sorted_cookies_path = Path(sorted_cookies_dir, site_dir.split('/')[-1])
    if not os.path.exists(sorted_cookies_path):
        os.mkdir(sorted_cookies_path)

    sorted_cookies_path = Path('analyze/data/sorted_cookies', site_dir.split('/')[-1])
    if not os.path.exists(sorted_cookies_path):
        os.mkdir(sorted_cookies_path)

    logsPath = utilities.get_files_in_a_directory(site_dir)
    for logfile in logsPath:
        if logfile.split('/')[-1].split('.')[0] == 'cookielogs':
            with open(str(logfile), 'r') as file:
                for line in file:
                    cookieLogs = json.loads(line.strip())
                    data.append(cookieLogs)

            sorted_entries = sorted(data, key=lambda x: x['timestamp'])

    with open(Path(sorted_cookies_path, 'cookielogs.json'), 'w') as output_file:
        json.dump(sorted_entries, output_file, indent=4)