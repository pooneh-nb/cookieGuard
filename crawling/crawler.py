import os
import time
import signal
import random
import tempfile
import signal
import shutil
import utilities
import subprocess
from urllib.parse import urlparse
from pathlib import Path
from multiprocessing import Process
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def kill_chrome():
    try:
        output = subprocess.check_output(["pgrep", "chrome"]).decode().strip().split("\n")
        for pid in output:
            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                print(f"⚠️ Process {pid} already exited.")
        print("✅ Killed all running Chrome processes.")
    except subprocess.CalledProcessError:
        print("ℹ️ No Chrome processes were running.")

def get_base_domain(u):
    parsed = urlparse(u)
    return parsed.netloc.replace("www.", "")

def is_internal_link(base, href):
    if not href:
        return False
    if href.startswith("/"):
        return True
    try:
        return base in get_base_domain(href)
    except:
        return False

def random_click(driver, url):
    print("click?")
    max_clicks = 3
    clicked = 0
    attempts = 0
    max_attempts = 10

    base = get_base_domain("https://" + url)

    links = driver.find_elements(By.TAG_NAME, 'a')
    internal_links = [l for l in links if is_internal_link(base, l.get_attribute('href'))]
    random.shuffle(internal_links)

    for link in internal_links:
        if clicked >= max_clicks or attempts >= max_attempts:
            break

        href = link.get_attribute('href')
        if not href or not link.is_displayed() or not link.is_enabled():
            continue

        attempts += 1  # ✅ always count the attempt

        try:
            print("start clicking")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", link)
            time.sleep(1)
            link.click()
            clicked += 1
            time.sleep(2)
            driver.back()
            time.sleep(2)
        except Exception as e:
            print(f"❌ Could not click link: {e}")

    print(f"🔚 Clicked {clicked} link(s) in {attempts} attempts.")

def load_url(url, chromedriver_path, sleep):
    temp_profile = tempfile.mkdtemp(prefix="chrome-profile-")

    chrome_options = Options()
    chrome_options.binary_location = "/opt/google/chrome/google-chrome"
    chrome_options.add_argument(f"user-data-dir={temp_profile}")
    # chrome_options.add_argument("user-data-dir=/tmp/fresh-profile")
    chrome_options.add_argument("profile-directory=Profile 20")
    chrome_options.add_argument("--load-extension=/home/c6/cookieProtect/cookieInterceptor/extension")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.set_page_load_timeout(sleep + 2)
        driver.get("https://" + url)
        time.sleep(sleep)
        driver.execute_script("window.scrollBy(0, 100)")
        random_click(driver, url)
        print(f"✅ Finished: {url}")

    except Exception as e:
        print(f"❌ Error loading {url}: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        try:
            shutil.rmtree(temp_profile)
        except Exception as e:
            print(f"❌ Failed to delete profile dir {temp_profile}: {e}")


def run(urls, chromedriver_path, sleep):
    for idx, url in enumerate(urls):
        if idx > 3300:
            print(f"\n🌐 {idx} Visiting: {url}")
            load_url(url, chromedriver_path, sleep)
        # p = Process(target=load_url, args=(url, chromedriver_path, sleep))
        # p.start()
        # p.join(sleep + 10)  # hard timeout per site

        # if p.is_alive():
        #     print(f"🛑 Force killing stalled load: {url}")
        #     p.terminate()
        #     p.join()
        #     kill_chrome()


if __name__ == "__main__":
    kill_chrome()
    CHROMEDRIVER = str(Path(Path.cwd(), 'crawling/chromedriver/chromedriver-linux64/chromedriver'))
    tranco = str(Path(Path.cwd(), 'crawling/tranco/sites_sh.txt'))

    SLEEP = 10

    with open(tranco, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    visited_sites_raw = utilities.get_directories_in_a_directory(Path(Path.cwd(), 'cookieInterceptor/server/output'))
    visited_sites = [url.split('/')[-1] for url in visited_sites_raw]

    unvisited_sites = [url for url in urls if url not in visited_sites]
    
    run(unvisited_sites, CHROMEDRIVER, SLEEP)