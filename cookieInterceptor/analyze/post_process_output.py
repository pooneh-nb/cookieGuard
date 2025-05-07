import utilities
from pathlib import Path
import shutil

output_path = Path(Path.cwd(), 'cookieInterceptor/server/output')

output = utilities.get_directories_in_a_directory(output_path)

count = 0
for site in output:
    files = utilities.get_files_in_a_directory(site)
    if len(files) <= 1:
        print(site.split('/')[-1])
        shutil.rmtree(site)
        count += 1
print(count)