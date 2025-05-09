import sys
import os
import re
import time
import tldextract
from pathlib import Path
project_dir = Path.home().cwd()
sys.path.insert(1, Path.home().joinpath(project_dir).as_posix())
sys.path.insert(1, Path.home().joinpath(project_dir, "analysis").as_posix())
sys.path.insert(1, Path.home().joinpath(project_dir, "filterlists").as_posix())
import utilities
import itertools
from tqdm import tqdm
from datetime import datetime
import check_tracking_single_url
import identifier_sharing as idSync
from urllib.parse import urlparse, urlunparse
import multiprocessing
from multiprocessing.pool import Pool



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
    # raise ValueError(f"date_str does not match any supported format")
    return None


def is_3p(url1, url2):
    return check_tracking_single_url.get_domain(url1) != check_tracking_single_url.get_domain(url2)


def is_sneaky_exfiltration(query_ids, hashes):
    sneaky_exfiltration = []
    for qid in query_ids:
        for key, algo in hashes:
            for algo_name, algo_value in algo.items():
                if qid == algo_value:
                    sneaky_exfiltration.append((key, algo_name))
    return sneaky_exfiltration


def run_exfiltration_process(siteName, storage_dict, requests, hash_values):
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
    parts = raw_cookie.split(';')
    cookie_data = {}

    # Extract cookie name and value
    if parts and '=' in parts[0]:
        name, value = parts[0].split('=', 1)
        cookie_data['name'] = name.strip()
        cookie_data['value'] = value.strip()
    else:
        cookie_data['name'] = parts[0].strip() if parts else ''
        cookie_data['value'] = ''

    # Extract attributes like Domain, Path, Secure, etc.
    for part in parts[1:]:
        part = part.strip()
        if '=' in part:
            key, val = part.split('=', 1)
            key = key.strip().lower()
            val = val.strip()
            if key == 'domain':
                try:
                    val = check_tracking_single_url.get_domain(val)
                except Exception:
                    pass  # fail silently if domain check fails
            cookie_data[key] = val
        elif part:  # for flags like Secure, HttpOnly
            cookie_data[part.lower()] = True

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
                if parsed_date is not None:
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


def moderator(args):
    sorted_cookie, common_headers, hash_values, output_dir = args
    siteName = sorted_cookie.split('/')[-1]
    try:
        cookieLogs_path = utilities.get_files_in_a_directory(sorted_cookie)[0]
        storage_dict = {siteName: {}}

        if os.path.getsize(cookieLogs_path) < 2:
            return None

        transactions = utilities.read_json(cookieLogs_path)
        for transaction in transactions:
            if transaction["action"] == "set":
                storage_dict = write_storage(transaction, storage_dict, siteName, common_headers)
            elif transaction["action"] == "get":
                storage_dict = read_storage(transaction, storage_dict, siteName)

        if not any(storage_dict[siteName].values()):
            return None

        requests_path = Path(Path.cwd(), f"cookieInterceptor/analyze/data/sorted_requests/{siteName}/requestlogs.json")
        if requests_path.exists():
            requests = utilities.read_json(requests_path)
            run_exfiltration_process(siteName, storage_dict, requests, hash_values)

        out_path = output_dir / f"storage_{siteName}.json"
        utilities.write_json(out_path, storage_dict)
        return siteName
    except Exception as e:
        print(f"❌ Failed {siteName}: {e}")
        return None


def main():
    print("🔁 Creating per-site storage JSON files")

    sorted_cookies_path = Path(Path.cwd(), 'cookieInterceptor/analyze/data/sorted_cookies')
    sorted_cookies = utilities.get_directories_in_a_directory(sorted_cookies_path)

    common_headers_path = Path(Path.cwd(), "cookieInterceptor/analyze/data/common_headers.txt")
    common_headers = set(
        line.strip().lower()
        for line in utilities.read_file_newline_stripped(common_headers_path)
        if line.strip()
    )

    hash_data = utilities.read_json(Path(Path.cwd(), "cookieInterceptor/analyze/data/algos.json"))
    hash_values = [v for algo in hash_data.values() for v in algo.values()]

    output_dir = Path(Path.cwd(), "cookieInterceptor/analyze/data/storage_sites")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 Starting parallel site processing with Pool")
    cpu_to_relax = 2
    args = zip(
        sorted_cookies,
        itertools.repeat(common_headers),
        itertools.repeat(hash_values),
        itertools.repeat(output_dir)
    )

    cpu_to_relax = 2
    with Pool(processes=multiprocessing.cpu_count() - cpu_to_relax) as pool:
        for _ in tqdm(pool.imap_unordered(moderator, args), total=len(sorted_cookies), desc="Processing sites"):
            pass  # tqdm updates per completed site


    print("✅ Finished per-site processing. Merging...")
    merged_dict = {}

    for file in output_dir.glob("storage_*.json"):
        site_dict = utilities.read_json(file)
        merged_dict.update(site_dict)

    final_output = Path(Path.cwd(), "cookieInterceptor/analyze/data/storage_dict.json")
    utilities.write_json(final_output, merged_dict)
    print(f"✅ All done. Final storage_dict saved to {final_output}")

if __name__ == "__main__":
    main()
    





