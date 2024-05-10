from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

import csv
import os
import json

from pathlib import Path
import utilities


# Initialize Chrome Driver


def get_performance_data(url):
    # service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-data-dir={'/home/c6/.config/google-chrome/Profile 3'}")
    
    driver_path = '/home/c6/Downloads/chromedriver-linux64/chromedriver'
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Navigate to the URL
        driver.delete_all_cookies()
        driver.set_page_load_timeout(30) # sets the time Selenium will wait for a page load to complete before throwing a TimeoutException
        driver.get(url=r"https://" + url)

        # Execute JavaScript to extract performance timing
        performance_timing = driver.execute_script("return window.performance.timing")

        # Calculate the metrics
        dom_content_loaded = performance_timing['domContentLoadedEventEnd'] - performance_timing['navigationStart']
        dom_interactive = performance_timing['domInteractive'] - performance_timing['navigationStart']
        load_event_time = performance_timing['loadEventEnd'] - performance_timing['navigationStart']

        # driver.quit()
        # os.system("pkill chrome")
        # Print or return the performance data
        return {"url": url, 
            "dom_content_loaded": dom_content_loaded,
            "dom_interactive": dom_interactive,
            "load_event_time": load_event_time}
    except Exception as e:
        print(e, url)
        driver.quit()
        os.system("pkill chrome")
        pass
    finally:
        driver.quit()
        os.system("pkill chrome")




sites_path = Path(Path.cwd(), "performance/tranco.csv")

visited_sites_path = Path(Path.cwd(), 'performance/visited.json')
visited_sites = utilities.read_json(visited_sites_path)
visited_sites = visited_sites[:-1]

performance_path = Pa-th(Path.cwd(), 'performance/performance_EXTENSION.json')
performance_list = utilities.read_json(performance_path)

# Measure performance for each URL
try:
    with open(sites_path, mode='r', newline='', encoding='utf-8') as file:
        
        # Create a CSV reader
            sites = csv.reader(file)
            for url in sites:
                url = url[0]
                if url not in visited_sites:
                    visited_sites.append(url)
                    with open(visited_sites_path, 'w') as file:
                        json.dump(visited_sites, file, indent=4) 
                    print(url)
                    obj = get_performance_data(url)
                    if obj:
                        performance_list.append(obj)
                        with open('performance/performance_EXTENSION.json', 'w') as f:
                            json.dump(performance_list, f, indent=4)

except Exception as e:
    os.system("pkill chrome")
    print(e, url)




