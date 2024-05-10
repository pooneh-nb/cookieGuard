import utilities
import json
from pathlib import Path

def read_and_extract_urls(data_path):
    visited = []
    try:
        data = utilities.read_json(data_path)
        for r in data:
           print(r)
           visited.append(r['url'])
        return visited

    except Exception as e:
        print(f"An error occurred: {e}")
        pass   

data_path = Path(Path.cwd(), 'performance/performance_EXTENSION.json')
visited_list = read_and_extract_urls(data_path)
visited_path = Path(Path.cwd(), 'performance/visited.json')
utilities.write_json(visited_path ,visited_list)

