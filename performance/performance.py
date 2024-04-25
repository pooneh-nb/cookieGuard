from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import csv
import json
import time
import pandas as pd
from pathlib import Path

def get_performance_data(url):
    # Setting up the Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument(f"user-data-dir={'/home/pooneh/.config/google-chrome/Profile 9'}")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Navigate to the URL
        driver.delete_all_cookies()
        driver.set_page_load_timeout(30) # sets the time Selenium will wait for a page load to complete before throwing a TimeoutException
        driver.get(url=r"https://" + url)
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Execute JavaScript to extract performance timing
        performance_timing = driver.execute_script("return window.performance.timing")

        # Calculate the metrics
        dom_content_loaded = performance_timing['domContentLoadedEventEnd'] - performance_timing['navigationStart']
        dom_interactive = performance_timing['domInteractive'] - performance_timing['navigationStart']
        load_event_time = performance_timing['loadEventEnd'] - performance_timing['navigationStart']

        driver.quit()
        # Print or return the performance data
        return {
            "url": url,
            "dom_content_loaded": dom_content_loaded,
            "dom_interactive": dom_interactive,
            "load_event_time": load_event_time
        }
    finally:
        # Close the WebDriver
        driver.quit()

# List of URLs to test
sites_path = Path(Path.cwd(), "performance/tranco.csv")
# urls = ["facebook.com", "www.google.com"]

performance = []
# Measure performance for each URL

try:
    with open(sites_path, mode='r', newline='', encoding='utf-8') as file:
        
        # Create a CSV reader
            sites = csv.reader(file)
            for url in sites:
                print(url[0])
                obj = get_performance_data(url[0])
                # performance.append(obj)
                with open('performance_EXTENSION.json', 'a') as f:
                    json.dump(obj, f, indent=4)

except Exception as e:
    print(e, url)
    pass




