import re
import os
import json
import utilities
from pathlib import Path
import tldextract
import identifier_sharing as idSync
from urllib.parse import urlparse, urlunparse


def clear_url(url):
    # if url == 'https://www.google-analytics.com/analytics.js:93:117)':
    #     print("y")
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"
    parsed_url = urlparse(url)
    path_without_line_col = re.sub(r':\d+:\d+$', '', parsed_url.path)
    query_without_line_col = re.sub(r':\d+:\d+$', '', parsed_url.query)
    full_path = urlunparse(('', '', path_without_line_col, '', query_without_line_col, ''))
    result = f"{domain}{full_path}"
    return result

def main():
    print("sort_requesrs_2:")

    crawls_path = Path('server/output')

    sites_dirs = utilities.get_directories_in_a_directory(crawls_path)

    for site_dir in sites_dirs:
        data = []
        sorted_requests_dir = Path('analyze/data/sorted_requests')
        if not os.path.exists(sorted_requests_dir):
            os.mkdir(sorted_requests_dir)
        sorted_requests_path = Path(sorted_requests_dir, site_dir.split('/')[-1])
        if not os.path.exists(sorted_requests_path):
            os.mkdir(sorted_requests_path)

        logsPath = utilities.get_files_in_a_directory(site_dir)
        for logfile in logsPath:
            if logfile.split('/')[-1].split('.')[0] == 'requestlogs':
                with open(str(logfile), 'r') as file:
                    for line in file:
                        requestLogs = json.loads(line.strip())
                        # extract identifiers
                        request_url = requestLogs['requestURL']
                        requestLogs['initiatorURL'] = clear_url(requestLogs['initiatorURL'])
                        query = idSync.get_query(request_url)
                        identifiers = set()
                        identifiers |= idSync.get_identifiers_from_qs(query)
                        requestLogs['identifiers'] = list(identifiers) 
                        data.append(requestLogs)

                sorted_entries = sorted(data, key=lambda x: x['timestamp'])

        with open(Path(sorted_requests_path, 'requestlogs.json'), 'w') as output_file:
            json.dump(sorted_entries, output_file, indent=4)
    print("done!")

if __name__ == "__main__":
    main()