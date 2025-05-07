from urllib.parse import urlparse, urlunparse

import utilities
from pathlib import Path
import tldextract
import re

def main():
    print("extracting valid cookie names")
    storage_dict = utilities.read_json(Path(Path.cwd(), 'cookieInterceptor/analyze/data/storage_dict.json'))

    keys = set()
    for site, cookies in storage_dict.items():
        for cookie_name, cookie_info in cookies.items():
            for key, val in cookie_info.items():
                if type(val) != bool:
                    if len(val) > 8:
                        keys.add(key)

    utilities.write_json(Path(Path.cwd(), 'cookieInterceptor/analyze/data/cookie_parameters.json'), list(keys))

if __name__ == "__main__":
    main()
