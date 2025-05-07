import utilities
from pathlib import Path


def is_session_cookie(cookie_details):
    if 'expires' not in cookie_details.keys() and 'max-age' not in cookie_details.keys():
        return True
    return False

def detect_session_cookies(storage_dict, session_cookies):
    for domain, cookies in storage_dict.items():
        for cookie_name, cookie_details in cookies.items():
            if is_session_cookie(cookie_details):
                if domain not in session_cookies:
                    session_cookies[domain] = {}
                session_cookies[domain][cookie_name] = cookie_details
                # session_cookies[domain][cookie_name]['logs'] = []          
                

def main():

    print("Collecting session cookies!")
    session_cookies = {}
    storage_dict = utilities.read_json(Path(Path.cwd(), 'analyze/data/storage_dict.json'))
    detect_session_cookies(storage_dict, session_cookies)


    path_to_session_cookies = Path('analyze/data/session_cookies.json')
    utilities.write_json(path_to_session_cookies, session_cookies)


if __name__ == "__main__":
    main()
                