import sys
from pathlib import Path
project_dir = Path.home().cwd()
sys.path.insert(1, Path.home().joinpath(project_dir).as_posix())
sys.path.insert(1, Path.home().joinpath(project_dir, "analysis").as_posix())
sys.path.insert(1, Path.home().joinpath(project_dir, "filterlists").as_posix())
import check_tracking_single_url
import utilities
import identifier_sharing as idSync
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
import tldextract
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from datetime import datetime, timezone

def clear_url(url):
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"
    parsed_url = urlparse(url)
    path_without_line_col = re.sub(r':\d+:\d+$', '', parsed_url.path)
    query_without_line_col = re.sub(r':\d+:\d+$', '', parsed_url.query)
    full_path = urlunparse(('', '', path_without_line_col, '', query_without_line_col, ''))
    result = f"{domain}{full_path}"
    return result

def parse_date(date_str):
    formats = [
        "%a, %d-%b-%Y %H:%M:%S %Z",  # Mon, 01-Jan-1990 00:00:00 GMT
        "%a, %d %b %Y %H:%M:%S %Z",   # Mon, 01 Jan 1990 00:00:00 GMT
        "%a %b %d %Y %H:%M:%S"  # Mon Mar 09 2026 20:28:42 GMT-0700 (Pacific Daylight Time)
    ]
    date_str = re.sub(r' GMT[+-]\d{4} \(\w+\s\w+\s\w+\)', '', date_str).strip()
    for date_format in formats:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    raise ValueError(f"date_str does not match any supported format")


def is_3p(url1, url2):
    is_3p = check_tracking_single_url.get_domain(url1) != check_tracking_single_url.get_domain(url2)
    return is_3p

def is_sneaky_exfiltration(query_ids, hashes):
    sneaky_exfiltration = []
    for qid in query_ids:
        for key, algo in hashes:
            for algo_name, algo_value in algo.items():
                if qid == algo_value:
                    sneaky_exfiltration.append((key, algo_name))
    return sneaky_exfiltration



def run_exfiltration_process(siteName, storage_dict):
    hashes = utilities.read_json(Path(Path.cwd(), "cookieInterceptor/analyze/data/algos.json"))
    hash_values = []
    for field, value in hashes.items():
        for alg, hash in value.items():
            hash_values.append(hash)
            

    requests_dir = Path(Path.cwd(), f"cookieInterceptor/analyze/data/sorted_requests/{siteName}/requestlogs.json")
    requests = utilities.read_json(requests_dir)
    for key, value in storage_dict[siteName].items():
        cookie_ids = storage_dict[siteName][key]['identifiers']
        exfiltration = {}
        for request in requests:
            # Any party other than the owner of the cookie exfiltrate identifiers
            if value['owner']['timeStamp'] <= request['timestamp']:
                if is_3p(request['initiatorURL'], storage_dict[siteName][key]['owner']['initiatorURL']):
                    query_ids = request['identifiers']
                    if cookie_ids and query_ids:

                        status, exfiltrated, data = idSync.run_idsyncing_heuristic(cookie_ids, query_ids, hash_values)
                        if status:
                            storage_dict[siteName][key]['logs'].append({'action': 'exfiltration',
                                                                    'initiatorURL': request['initiatorURL'],
                                                                    'destination': request['requestURL'],
                                                                    'identifiers': exfiltrated,
                                                                    'exfiltrated_hash': data,
                                                                    'timeStamp': request['timestamp']})
    return storage_dict

def get_cookie_params(raw_cookie):
    # Regular expression to extract key-value pairs
    parts = raw_cookie.split(';')
    cookie_data = {}
    
    # First part is always the cookie name and value
    name, value = parts[0].split('=', 1)
    cookie_data['name'] = name.strip()
    cookie_data['value'] = value.strip()
    
    # Parsing additional parameters if they exist
    for part in parts[1:]:
        if '=' in part:
            key, val = part.split('=', 1)
            if key == 'domain':
                val = check_tracking_single_url.get_domain(val)
            cookie_data[key.strip().lower()] = val.strip()
        else:
            cookie_data[part.strip().lower()] = True  # For flags like 'secure' and 'HttpOnly' which have no value

    return cookie_data


def write_storage(transaction, storage_dict, siteName, common_headers):
    raw_cookie = transaction['cookie'].strip()
    cookie_params = get_cookie_params(raw_cookie)
    initiatorURL = clear_url(transaction['initiatorURL'])
    visitingDomain = transaction['visitingDomain']
    action = transaction['action']
    accessType = transaction['accessType']
    if accessType == 'http':
        cookieType = 'httpCookie'
    else:
        cookieType = transaction['cookieType']
    timestamp = transaction['timestamp']

    cookie_name = cookie_params.get('name')

    # cookie is observed before. Either deleting or overwriting is happening
    if cookie_name in storage_dict[siteName]:
         # check if deletig happens
        if cookie_params.get('value') == "" or cookie_params.get('max-age') == 0:
            delete_storage(transaction, storage_dict, siteName)
            return storage_dict
        if 'expires' in cookie_params:
            specific_time = datetime(2025, 2, 10, 17, 0, 0)
            # expires_datetime = datetime.strptime(cookie_params['expires'], date_format)
            try:
                parsed_date = parse_date(cookie_params['expires'])
                if parsed_date < specific_time:
                    delete_storage(transaction, storage_dict, siteName)
                    return storage_dict
            except ValueError as e:
                pass
                print(e)  
        #  check if overwriting happens
        # if cookie_params.get('domain') and cookie_params['domain'].startswith('.'):
        #     cookie_params['domain'] = cookie_params['domain'][1:]
        if cookie_params.get('domain') == visitingDomain:
            if is_3p(initiatorURL, storage_dict[siteName][cookie_params['name']]['owner']['initiatorURL']): 
                cookies = {cookie_params['name']: cookie_params['value']}
                identifiers = idSync.get_identifier_cookies(cookies, common_headers)
                storage_dict[siteName][cookie_params['name']]['identifiers'].extend(identifiers)
                storage_dict[siteName][cookie_params['name']]['logs'].append({'action': 'overwriting',
                                                                            'value': cookie_params['value'],
                                                                            **{k: v for k, v in cookie_params.items() if k != 'name'},
                                                                            'initiatorURL': initiatorURL,
                                                                            'cookieAction': action,
                                                                            'cookieType': cookieType,
                                                                            'accessType': accessType,
                                                                            'timeStamp': timestamp})
            else: # Actions for non-3p
                cookies = {cookie_params['name']: cookie_params['value']}
                identifiers = idSync.get_identifier_cookies(cookies, common_headers)
                storage_dict[siteName][cookie_params['name']]['identifiers'].extend(identifiers)

    # cookie name is new. The request is to set a new cookie
    else:
        storage_dict[siteName][cookie_params['name']] = {}
        for key, value in cookie_params.items():
            if key != 'name':
                if key == "":
                    continue
                storage_dict[siteName][cookie_params['name']][key] = value
        cookies = {cookie_params['name']: cookie_params['value']}
        identifiers = idSync.get_identifier_cookies(cookies, common_headers)
        storage_dict[siteName][cookie_params['name']]['identifiers'] = [item for item in identifiers]
        storage_dict[siteName][cookie_params['name']]['owner'] = {'initiatorURL': initiatorURL, 'cookieAction': action, 'accessType': accessType, 'cookieType': cookieType,'timeStamp': timestamp}
        storage_dict[siteName][cookie_params['name']]['logs'] = []
        
    storage_dict[siteName][cookie_params['name']]['identifiers'] = list(set(storage_dict[siteName][cookie_params['name']]['identifiers']))
                                                                         
    return storage_dict
                        
def read_storage(transaction, storage_dict, siteName):
    raw_cookies = transaction['cookie']
    initiatorURL = clear_url(transaction['initiatorURL'])
    accessType = transaction['accessType']
    action = transaction['action']
    if accessType == 'http':
        cookieType = 'httpCookie'
    else:
        cookieType = transaction['cookieType']
    timestamp = transaction['timestamp']
    cookie_pairs = raw_cookies.split(';')

    for cookie_pair in cookie_pairs:
        name = cookie_pair.split('=')[0]
        if name in storage_dict[siteName]:
            if is_3p(initiatorURL, storage_dict[siteName][name]['owner']['initiatorURL']):
                storage_dict[siteName][name]['logs'].append({'action': 'retrieving',
                                                             'value': "",
                                                             'initiatorURL': initiatorURL,
                                                             'cookieAction': action,
                                                             'cookieType': cookieType,
                                                             'accessType': accessType,
                                                             'timeStamp': timestamp})
    return storage_dict

def delete_storage(transaction, storage_dict, siteName):
    raw_cookie = transaction['cookie']
    cookie_params = get_cookie_params(raw_cookie)
    initiatorURL = clear_url(transaction['initiatorURL'])
    visitingDomain = transaction['visitingDomain']
    action = transaction['action']
    accessType = transaction['accessType']
    if accessType == 'http':
        cookieType = 'httpCookie'
    else:
        cookieType = transaction['cookieType']
    timestamp = transaction['timestamp']


    if cookie_params['name'] in storage_dict[siteName]:
        if is_3p(initiatorURL, storage_dict[siteName][cookie_params['name']]['owner']['initiatorURL']):
            storage_dict[siteName][cookie_params['name']]['logs'].append({'action': 'deleting',
                                                                          'value': cookie_params['value'],
                                                                          **{k: v for k, v in cookie_params.items() if k != 'name'},
                                                                          'initiatorURL': initiatorURL,
                                                                          'cookieAction': action,
                                                                          'cookieType': cookieType,
                                                                          'accessType': accessType,
                                                                          'timeStamp': timestamp})
    return storage_dict


def moderator(cookieLogs_path, storage_dict, common_headers):
    siteName = cookieLogs_path.split('/')[-2]
    storage_dict.setdefault(siteName, {})

    if os.path.getsize(cookieLogs_path) > 2:
        transactions = utilities.read_json(cookieLogs_path)
        for transaction in transactions:
                # write / overwrite / detele
                if transaction["action"] == "set":
                    dict_cookie = write_storage(transaction, storage_dict, siteName, common_headers)
                    continue
        
                # Read (keep track of cross-reading only)
                if transaction["action"] == "get":
                    dict_cookie = read_storage(transaction, storage_dict, siteName)
                    continue
            
        if storage_dict[siteName]:
            run_exfiltration_process(siteName, dict_cookie)
            # dict_cookie = run_unify_logs(dict_cookie)
    else:
        storage_dict[siteName] = {}

def main():
    print("create_storage_logs_3")
    # load data
    sorted_cookies_path = Path(Path.cwd(), 'cookieInterceptor/analyze/data/sorted_cookieStore')
    sorted_cookies = utilities.get_directories_in_a_directory(sorted_cookies_path)
    storage_dict = {}

    # common headers
    common_headers_dir = Path(Path.cwd(), "cookieInterceptor/analyze/data/common_headers.txt")
    known_http_headers_raw = utilities.read_file_newline_stripped(common_headers_dir)
    common_headers = set()
    for item in known_http_headers_raw:
        if item.strip() != '':
            common_headers.add(item.strip().lower())


    for sorted_cookie in sorted_cookies:
        sorted_cookieLogs_path = utilities.get_files_in_a_directory(sorted_cookie)[0]
        moderator(sorted_cookieLogs_path, storage_dict, common_headers)

    output = Path(Path.cwd(), 'cookieInterceptor/analyze/data')
    print("storing storage_dict.json")
    utilities.write_json(Path(output, "storage_dict.json"), storage_dict)
    print("done!")

if __name__ == "__main__":
    main()
    





