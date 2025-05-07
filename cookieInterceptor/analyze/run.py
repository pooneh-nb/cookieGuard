import sys
from pathlib import Path
sys.path.insert(1, Path(Path.cwd(), 'analyze').as_posix())

import sort_cookies_1
import sort_requests_2
import sort_cookieStore_3
import cookieInterceptor.analyze.create_regular_storage_logs_3 as create_regular_storage_logs_3
import extract_cookie_values_4
import significant_manipulation_detector_5


sort_cookies_1.main()
sort_requests_2.main()
sort_cookieStore_3.main()
create_regular_storage_logs_3.main()
extract_cookie_values_4.main()
significant_manipulation_detector_5.main()