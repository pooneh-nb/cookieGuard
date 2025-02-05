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

def is_3p(url1, url2):
    is_3p = check_tracking_single_url.get_domain(url1) != check_tracking_single_url.get_domain(url2)
    return is_3p


def run_exfiltration_process(site_name, dict_storage):
    responses_dir = Path.home().joinpath(Path.home().cwd(), "analysis/data/responses/responses_sorted/"+site_name+".json")
    responses = utilities.read_json(responses_dir)
    for key in dict_storage:
        cookie_ids = dict_storage[key]['identifiers']
        exfiltration = {}
        for response in responses:
            # Any party other than the owner of the cookie exfiltrate identifiers
            if is_3p(response['script_info']['script_url'], dict_storage[key]['owner']['script_info']['script_url']):
                query_ids = response['identifiers']
                if cookie_ids and query_ids:
                    status, exfiltrated = idSync.run_idsyncing_heuristic(cookie_ids, query_ids)
                    if status:
                        id = response['script_info']['script_node_id']
                        if id not in exfiltration:
                            exfiltration[id] = {}
                            exfiltration[id]['script_info'] = ""
                            exfiltration[id]['timestamp'] = []
                            exfiltration[id]['requested_url'] = set()
                            exfiltration[id]['identifiers'] = []
                        
                        exfiltration[id]['script_info'] = response['script_info']
                        exfiltration[id]['timestamp'].append(response['timestamp'])
                        exfiltration[id]['requested_url'].add(response['requested_url'])
                        exfiltration[id]['identifiers'].extend(exfiltrated)

        for id in exfiltration:
            exfiltration[id]['identifiers'] = list(set(exfiltration[id]['identifiers']))
            exfiltration[id]['requested_url'] = list(exfiltration[id]['requested_url'])
        dict_storage[key]['exfiltration'] = exfiltration
    return dict_storage

def write_storage(storage, dict_storage, common_headers):
    if storage['value'].startswith(';'):
       delete_storage(storage, dict_storage, 'semidelete')
       return dict_storage
    if storage['key'] not in dict_storage:
        dict_storage[storage['key']] = {}
        cookies = {storage['key']: storage['value'].split(';')[0]}
        identifiers = idSync.get_identifier_cookies(cookies, common_headers)
        dict_storage[storage['key']]['identifiers'] = [item for item in identifiers]       
        # owner info
        dict_storage[storage['key']]['owner'] = {'timestamp':storage['timestamp'],                                                  
                                                 'script_info':storage['script_info'], 
                                                 'action':storage['storage_action'],
                                                 'value': storage['value']}
        dict_storage[storage['key']]['logs'] = []
    else:
        if is_3p(storage['script_info']['script_url'], dict_storage[storage['key']]['owner']['script_info']['script_url']):
            cookies = {storage['key']: storage['value']}
            identifiers = idSync.get_identifier_cookies(cookies, common_headers)
            dict_storage[storage['key']]['identifiers'].extend(identifiers)
            dict_storage[storage['key']]['logs'].append({'timestamp':storage['timestamp'], 
                                                        'script_info':storage['script_info'], 
                                                        'action':storage['storage_action'],
                                                        'value': storage['value']})
        else:
            cookies = {storage['key']: storage['value']}
            identifiers = idSync.get_identifier_cookies(cookies, common_headers)
            dict_storage[storage['key']]['identifiers'].extend(identifiers)

    dict_storage[storage['key']]['identifiers'] = list(set(dict_storage[storage['key']]['identifiers']))
    return dict_storage
                        
def read_storage(storage, dict_storage):
    value = storage['value']
    value_pairs = value.split(';')
    for pair in value_pairs:
        key_ = pair.split('=')[0]
        # value_ = pair.split('=')[-1]
        if key_ in dict_storage:
            if is_3p(storage['script_info']['script_url'], dict_storage[key_]['owner']['script_info']['script_url']):
                dict_storage[key_]['logs'].append({'timestamp':storage['timestamp'], 
                                                'script_info':storage['script_info'], 
                                                'action':storage['storage_action'],
                                                'value': ""})
    return dict_storage

def delete_storage(storage, dict_storage, delete_type):
    if delete_type == 'semidelete':
        if storage['key'] in dict_storage:
            if is_3p(storage['script_info']['script_url'], dict_storage[storage['key']]['owner']['script_info']['script_url']):
                dict_storage[storage['key']]['logs'].append({'timestamp':storage['timestamp'], 
                                                        'script_info':storage['script_info'], 
                                                        'action': 'DeleteStorage',
                                                        'value': ""})

    else:
        if storage['key'] in dict_storage:
            if is_3p(storage['script_info']['script_url'], dict_storage[storage['key']]['owner']['script_info']['script_url']):
                dict_storage[storage['key']]['logs'].append({'timestamp':storage['timestamp'], 
                                                            'script_info':storage['script_info'], 
                                                            'action':storage['storage_action'],
                                                            'value': ""})
    return dict_storage

def clear_storage(storage, dict_storage):
    if storage['key'] in dict_storage:
        if is_3p(storage['script_info']['script_url'], dict_storage[storage['key']]['owner']['script_info']['script_info']['script_url']):
            dict_storage[storage['key']]['logs'].append({'timestamp':storage['timestamp'], 
                                                        'script_info':storage['script_info'], 
                                                        'action':storage['storage_action'],
                                                        'value': ""})
    return dict_storage


def main(cookies_sorted_dir, output):
    # common headers
    common_headers_dir = Path.home().joinpath(Path.cwd(), "analysis/data/common_headers.txt")
    known_http_headers_raw = utilities.read_file_newline_stripped(common_headers_dir)
    common_headers = set()
    for item in known_http_headers_raw:
        if item.strip() != '':
            common_headers.add(item.strip().lower())

    # cookies_sorted_dir = Path.home().joinpath(project_dir, "analysis/data/top_10k/cookies/cookie_sorted")
    cookies_sorted = utilities.get_files_in_a_directory(cookies_sorted_dir)
    # output = Path.home().joinpath(Path.cwd(), "analysis/data/top_10k/cookies")
    
    storage_dict = {}
    for site in tqdm(cookies_sorted, total=len(cookies_sorted)):
        site_name = site.split('/')[-1].split('.json')[0]
        storage_dict[site_name] = {}
        if os.path.getsize(site) > 2:
            dict_cookie = {}
            dict_session_storage = {}
            dict_local_storage = {}
            content = utilities.read_json(site)
            for storage in content:
                ####### cookieJar analysis #######
                ##################################
                if storage['storage_type'] == "CookieJar":
                    # write
                    if storage["storage_action"] == "StorageSet":
                        dict_cookie = write_storage(storage, dict_cookie, common_headers)
                        continue
            
                    # Read (keep track of cross-reading only)
                    if storage["storage_action"] == "StorageReadResult":
                        dict_cookie = read_storage(storage, dict_cookie)
                        continue
                        
                                
                    # Delete (keep track of cross-deleting only)
                    if storage["storage_action"] == "DeleteStorage":
                        dict_cookie = delete_storage(storage, dict_cookie, 'normal')
                        continue
                        

                    # clear (keep track of cross-clearing only)
                    if storage["storage_action"] == "ClearStorage":
                        dict_cookie = clear_storage(storage, dict_cookie)
                        continue
                        
                    if storage["storage_action"] == "ReadStorageCall":
                        continue

                ###### SessionStorage analysis ######
                #####################################
                if storage['storage_type'] == "SessionStorage":
                    # write
                    if storage["storage_action"] == "StorageSet":
                        dict_session_storage = write_storage(storage, dict_session_storage, common_headers)
                        continue
            
                    # Read (keep track of cross-reading only)
                    if storage["storage_action"] == "StorageReadResult":
                        dict_session_storage = read_storage(storage, dict_session_storage)
                        continue
                        
                                
                    # Delete (keep track of cross-deleting only)
                    if storage["storage_action"] == "DeleteStorage":
                        dict_session_storage = delete_storage(storage, dict_session_storage, 'normal')
                        continue
                        

                    # clear (keep track of cross-clearing only)
                    if storage["storage_action"] == "ClearStorage":
                        dict_session_storage = clear_storage(storage, dict_session_storage)
                        continue
                        
                    if storage["storage_action"] == "ReadStorageCall":
                        continue
                
                ###### LocalStorage analysis #######
                ####################################
                if storage['storage_type'] == "LocalStorage":
                    # write
                    if storage["storage_action"] == "StorageSet":
                        dict_local_storage = write_storage(storage, dict_local_storage, common_headers)
                        continue
            
                    # Read (keep track of cross-reading only)
                    if storage["storage_action"] == "StorageReadResult":
                        dict_local_storage = read_storage(storage, dict_local_storage)
                        continue
                        
                                
                    # cook Delete (keep track of cross-deleting only)
                    if storage["storage_action"] == "DeleteStorage":
                        dict_local_storage = delete_storage(storage, dict_local_storage, 'normal')
                        continue
                        

                    # clear (keep track of cross-clearing only)
                    if storage["storage_action"] == "ClearStorage":
                        dict_local_storage = clear_storage(storage, dict_local_storage)
                        continue
                        
                    if storage["storage_action"] == "ReadStorageCall":
                        continue
            
            if dict_cookie:
                dict_cookie = run_exfiltration_process(site_name, dict_cookie)
                # dict_cookie = run_unify_logs(dict_cookie)
            if dict_local_storage:
                dict_local_storage = run_exfiltration_process(site_name, dict_local_storage)
                # dict_local_storage = run_unify_logs(dict_local_storage)
            if dict_session_storage:
                dict_session_storage = run_exfiltration_process(site_name, dict_session_storage)
                # dict_session_storage = run_unify_logs(dict_session_storage)
            
            storage_dict[site_name]['cookie'] = dict_cookie
            storage_dict[site_name]['local_storage'] = dict_local_storage
            storage_dict[site_name]['session_storage'] = dict_session_storage
        else:
            dict_cookie = {}
            dict_session_storage = {}
            dict_local_storage = {}
            storage_dict[site_name]['cookie'] = dict_cookie
            storage_dict[site_name]['local_storage'] = dict_local_storage
            storage_dict[site_name]['session_storage'] = dict_session_storage

    
    
    utilities.write_json(Path.home().joinpath(output, "storage_dict.json"), storage_dict)





