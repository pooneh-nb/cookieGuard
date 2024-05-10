import numpy as np
import utilities
from pathlib import Path

performance_extension_path = Path(Path.cwd(), 'performance/performance_EXTENSION.json')
performance_extension = utilities.read_json(performance_extension_path)

performance_no_extension_path = Path(Path.cwd(), 'performance/performance_NO_EXTENSION.json')
performance_no_extension = utilities.read_json(performance_no_extension_path)

extension_sites = set()
no_extension_sites = set()

# find sites cralwed in both configs
for record in performance_extension:
    if record["dom_content_loaded"] > 0 and record["dom_interactive"] > 0 and record["load_event_time"] > 0:
        extension_sites.add(record["url"])

for record in performance_no_extension:
    if record["dom_content_loaded"] > 0 and record["dom_interactive"] > 0 and record["load_event_time"] > 0:
        no_extension_sites.add(record["url"])

extension_records = {'dom_content_loaded': [], 'dom_interactive': [], 'load_event_time': []}
no_extension_records = {'dom_content_loaded': [], 'dom_interactive': [], 'load_event_time': []}

for record in performance_extension:
    if record["url"] in extension_sites and record["url"] in no_extension_sites:
        extension_records['dom_content_loaded'].append(record['dom_content_loaded'])
        extension_records['dom_interactive'].append(record['dom_interactive'])
        extension_records['load_event_time'].append(record['load_event_time'])


for record in performance_no_extension:
    if record["url"] in extension_sites and record["url"] in no_extension_sites:
        no_extension_records['dom_content_loaded'].append(record['dom_content_loaded'])
        no_extension_records['dom_interactive'].append(record['dom_interactive'])
        no_extension_records['load_event_time'].append(record['load_event_time'])


print("Extension")
print("==========================")
print("dom_content_loaded: ")
print("mean: ", np.mean(extension_records['dom_content_loaded']), 
      "median: ", np.median(extension_records['dom_content_loaded']))

print("dom_interactive: ")
print("mean: ", np.mean(extension_records['dom_interactive']), 
      "median: ", np.median(extension_records['dom_interactive']))

print("load_event_time: ")
print("mean: ", np.mean(extension_records['load_event_time']), 
      "median: ", np.median(extension_records['load_event_time']))


print("NO Extension")
print("==========================")
print("dom_content_loaded: ")
print("mean: ", np.mean(no_extension_records['dom_content_loaded']), 
      "median: ", np.median(no_extension_records['dom_content_loaded']))

print("dom_interactive: ")
print("mean: ", np.mean(no_extension_records['dom_interactive']), 
      "median: ", np.median(no_extension_records['dom_interactive']))

print("load_event_time: ")
print("mean: ", np.mean(no_extension_records['load_event_time']), 
      "median: ", np.median(no_extension_records['load_event_time']))

print(len(no_extension_records['dom_content_loaded']), len(extension_records['dom_content_loaded']))
print(len(no_extension_records['dom_interactive']), len(extension_records['dom_interactive']))
print(len(no_extension_records['load_event_time']), len(extension_records['load_event_time']))

print("MAX")
print(max(no_extension_records['dom_content_loaded']), max(extension_records['dom_content_loaded']))
print(max(no_extension_records['dom_interactive']), max(extension_records['dom_interactive']))
print(max(no_extension_records['load_event_time']), max(extension_records['load_event_time']))

print("MIN")
print(min(no_extension_records['dom_content_loaded']), min(extension_records['dom_content_loaded']))
print(min(no_extension_records['dom_interactive']), min(extension_records['dom_interactive']))
print(min(no_extension_records['load_event_time']), min(extension_records['load_event_time']))