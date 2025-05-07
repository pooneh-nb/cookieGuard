import base64
import hashlib
from pathlib import Path
from urllib import parse as URLparse
import re
import utilities


def check_idsyncing_heuristic(cookie_ids, query_ids):

    for identifier in cookie_ids: 
        base64_identifier = base64.b64encode(identifier.encode('utf-8')).decode('utf8')
        md5_identifier = hashlib.md5(identifier.encode('utf-8')).hexdigest()
        sha1_identifier = hashlib.sha1(identifier.encode('utf-8')).hexdigest()
        
        if identifier in query_ids:
            return True
        elif base64_identifier in query_ids:
           return True
        elif md5_identifier in query_ids:
            return True
        elif sha1_identifier in query_ids:
            return True
            
    return False

def check_idsyncing_heuristic_with_form_data(hashes, query_ids):
    for item in query_ids:
        if item in hashes:
            return True
    return False

def run_idsyncing_heuristic(cookie_ids, query_ids, hashes):
    
    num_idsharing = 0
    is_sharing = False
    exfiltrated = []
    data = []
    for item in query_ids:
        if check_idsyncing_heuristic(cookie_ids, item):
            is_sharing = True
            exfiltrated.append(item)
        if check_idsyncing_heuristic_with_form_data(hashes, query_ids):
            data.append(query_ids)

    return is_sharing, exfiltrated, data
    
def get_identifiers_from_qs(query, qs_item_length = 8):
    # qs = URLparse.parse_qsl(URLparse.urlsplit(url).query)
    qs_set = set()
    
    for item in query:
        qs_set |= set(re.split('[^a-zA-Z0-9_=-]', item[0]))
        qs_set |= set(re.split('[^a-zA-Z0-9_=-]', item[1]))
        
    qs_set = set([s for s in list(qs_set) if len(s) >= qs_item_length])
    return qs_set

def get_identifier_cookies(cookies, common_headers, cookie_length = 8):
    # get identifiers in cookies
    cookie_set = set()
    for key, value in cookies.items():
        if key not in common_headers:
            cookie_set |= set(re.split('[^a-zA-Z0-9_=-]',value))
            cookie_set.add(key)
    cookie_set = set([s for s in list(cookie_set) if len(s) >= cookie_length])
    return list(cookie_set)

def get_identifier_from_standard_cookie(cookies, cookie_length = 8):
    # common headers
    common_headers_dir = Path.home().joinpath(Path.cwd(), "analysis/data/common_headers.txt")
    known_http_headers_raw = utilities.read_file_newline_stripped(common_headers_dir)
    common_headers = set()
    for item in known_http_headers_raw:
        if item.strip() != '':
            common_headers.add(item.strip().lower())
    # get identifiers in cookies
    cookie_set = set()
    for key, value in cookies.items():
        if key not in common_headers:
            cookie_set |= set(re.split('[^a-zA-Z0-9_\-\.%]',value))
            cookie_set.add(key)

def get_query(url):
    query = URLparse.parse_qsl(URLparse.urlsplit(url).query)
    return query


def main():
    """
    The initial point to start detecting identifier sharing
    Required arguments to pass to functions:
        url: we extract queries out of urls and then extract identifiers
        cookie: key and values are considered as identifiers
    """
    """
        The order of calling these functions:
        1. query = get_query(url)
        2. query_identifiers = get_identifiers_from_qs(query)
        3. run_idsyncing_heuristic(cookie, query_identifiers)
    """

# identifiers = set()
# identifiers |= get_identifiers_from_qs(query)
# identifiers |= get_identifier_cookies(cookies, common_headers)