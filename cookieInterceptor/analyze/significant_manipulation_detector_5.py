import utilities
import check_tracking_single_url
from pathlib import Path

def significant_change(original, log):
    keys_to_check = utilities.read_json('analyze/data/cookie_parameters.json')
    for key in keys_to_check:
        if key in log and (key not in original or log[key] != original[key]):
            return True
        elif key in original and key not in log:
            return True
    return False

def is_session_cookie(cookie_details):
    if 'expires' not in cookie_details.keys() and 'max-age' not in cookie_details.keys():
        return True
    return False

def filter_significant_changes(storage_dict):
    for domain, cookies in storage_dict.items():
        cookies_to_keep = {}
        for cookie_name, cookie_details in cookies.items():
            initial_settings = {key: cookie_details[key] for key in cookie_details if (key != 'logs' and key != 'identifiers' and key != 'owner')}
            filtered_logs = []
            for log in cookie_details['logs']:
                if check_tracking_single_url.get_domain(log['initiatorURL']) != domain: # delete later
                    # if check_tracking_single_url.get_domain(log['initiatorURL']) != "googletagmanager.com" and \
                    #     check_tracking_single_url.get_domain(log['initiatorURL']) != "google-analytics.com":
                        if log['action'] in ['overwriting', 'deleting', 'exfiltration', 'retrieving']:
                        # if log['action'] in ['overwriting', 'deleting']:
                            if log['action'] == 'overwriting' and not significant_change(initial_settings, log):
                                continue
                            if log['action'] == 'exfiltration' and not is_session_cookie(cookie_details):
                                continue
                            filtered_logs.append(log)
            if filtered_logs:
                cookie_details['logs'] = filtered_logs
                cookies_to_keep[cookie_name] = cookie_details
        storage_dict[domain] = cookies_to_keep


def main():
    print("Collecting significant manipulations!")
    storage_dict = utilities.read_json(Path(Path.cwd(), 'cookieInterceptor/analyze/data/storage_dict.json'))
    filter_significant_changes(storage_dict)

    path_to_manipulated_logs = Path(Path.cwd(), 'cookieInterceptor/analyze/data/significant_manipulate.json')
    utilities.write_json(path_to_manipulated_logs, storage_dict)

if __name__ == "__main__":
    main()
                                
                                
