import utilities
from pathlib import Path

storage_dict = utilities.read_json(Path('analyze/data/storage_dict.json'))

for site, site_info in storage_dict.items():
    for cookieName, cookieValues in site_info.items():
        if len(cookieValues['logs'])