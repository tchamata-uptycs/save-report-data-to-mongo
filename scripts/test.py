from datetime import datetime,timedelta
import os
import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import concurrent.futures
import logging
logging.getLogger('seleniumwire').setLevel(logging.WARNING)
from  prometeus_utils import PrometheusConnector

executable_base_path = PrometheusConnector().base_stack_config_path
service = ChromeService(executable_path=f"{executable_base_path}/chromedriver")
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')

driver = webdriver.Chrome(service=service,options=chrome_options)
driver.get("http://192.168.128.50:3000/login")

l = [110,136,128,130]

driver.maximize_window()
wait = WebDriverWait(driver, 60)  #waits for _ seconds
try:
    wait.until(EC.visibility_of_element_located((By.NAME, "user"))).send_keys("admin")
except Exception as e:
    print("Error: login page not loaded in time : ", type(e).__name__, "-", str(e))
driver.find_element("name","password").send_keys("admin123")
driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
time.sleep(5)
for t_id in l:
    url = ("http://192.168.128.50:3000/d/0xQAxECVk/osqueryloadtest?orgId=1&from=now-3h&to=now&viewPanel=%s") % (t_id)
    driver.get(url)
    time.sleep(5)
    wait = WebDriverWait(driver, 30)  #waits for _ seconds
    try:
        try:
            print("waiting for canvas")
            wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"5\"]/div/div[2]/div/plugin-component/panel-plugin-graph/grafana-panel/ng-transclude/div/div[1]/canvas[2]")))
        except:
            print("editing the panel")
            edit_url = ("http://192.168.128.50:3000/d/0xQAxECVk/osqueryloadtest?orgId=1&from=now-3h&to=now&viewPanel=%s&editPanel=%s") % (t_id,t_id)
            driver.get(url)
            print("inside edit url")
            time.sleep(5)
            drop_down_xpath="//*[@id=\"reactRoot\"]/div/main/div[3]/div[2]/div/div/div[1]/div/div[2]/div/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div/div/div/div[1]/div[1]/div"
            data_source_input = driver.find_element("xpath",drop_down_xpath)
            
            data_source_input.clear()
            data_source_input.send_keys("Prometheus-1")
            driver.find_element("xpath","//*[@id=\"reactRoot\"]/div/main/div[3]/div[2]/nav/div[6]/button").click()
        title= wait.until(EC.visibility_of_element_located((By.XPATH, "//*/div[1]/header/div/h2"))).text

    except Exception as e:
        title = f"panel {t_id} not loaded in given time"
    print(f"{title} : {t_id}")
   
   