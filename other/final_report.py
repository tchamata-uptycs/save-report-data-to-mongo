from datetime import datetime
import os
from pathlib import Path
import prometeus_utils as prom
import time
from seleniumwire import webdriver
import time
from selenium.webdriver.common.by import By
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import concurrent.futures
from create_pdf import LoadTestReportNewPdf

start_time_str = '2023-08-02 15:56' 
end_time_str = '2023-08-02 20:56'
table_ids = [78 , 80 , 82] # table panel ids
start_margin = 10
end_margin = 10

GRAFANA_USERNAME="admin"
GRAFANA_PASSWORD="admin123"
GRAFANA_PORT = "3000"
SCREENSHOT_DIR="grafana_screenshots"
pdf_path = Path(f'results/report.pdf')

format_data = "%Y-%m-%d %H:%M"
start_time = datetime.strptime(start_time_str, format_data)
end_time = datetime.strptime(end_time_str, format_data)
start_time_epoch = int(start_time.timestamp() * 1000)
end_time_epoch = int(end_time.timestamp() * 1000)
db=prom.PrometheusConnector('s1monitor', '9090')
GRAFANA_DASH_IDS = []


def generate_grafana_trends(t_id):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("http://" + db.ip_address[0] + ":" + GRAFANA_PORT + "/" + "login")
    driver.maximize_window()
    time.sleep(15)
    driver.find_element("name","user").send_keys(GRAFANA_USERNAME)
    driver.find_element("name","password").send_keys(GRAFANA_PASSWORD)
    driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
    time.sleep(15)
    driver.get("http://"+db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest")
    time.sleep(10)
    if t_id in table_ids:
        ste = start_time_epoch
        ete = end_time_epoch
        url = ("http://"+db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest?orgId=1&from=%s&to=%s&viewPanel=%s") % (ste, ete, t_id)
    else:
        ste = start_time_epoch - (start_margin * (60 *1000))
        ete = end_time_epoch + (end_margin * (60 *1000))
        url = ("http://"+db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest?orgId=1&from=%s&to=%s&viewPanel=%s&refresh=1s") % (ste, ete, t_id)
    driver.get(url)
    time.sleep(5)
    wait = WebDriverWait(driver, 60000) 
    try:
        title= wait.until(EC.visibility_of_element_located((By.XPATH, "//*/div[1]/header/div/h2"))).text
    except:
        title="not found"
    driver.save_screenshot(f'{SCREENSHOT_DIR}/{t_id}_1_{title}.png')
    print(f"{t_id} : {title}")
    page_number = 2
    def filter(n):
        lst=[]
        for i in n:
            html = i.get_attribute("innerHTML")
            if "table-panel-page-link" in html:lst.append(i)
        return lst
    while(True):
        n = driver.find_elements(By.TAG_NAME, "li")
        n= filter(n)
        if len(n)==0:break
        last_html = n[-1].get_attribute("innerHTML")
        active_flag = 0
        for i in n:
            html = i.get_attribute("innerHTML")
            if "active" in html:active_flag=1
            if "active" not in html and active_flag==1:
                i.find_element(By.TAG_NAME , "a").click()
                time.sleep(1)
                driver.save_screenshot(f'{SCREENSHOT_DIR}/{t_id}_{page_number}_{title}.png')
                page_number += 1
                break
        if "active" in last_html:
            break
    driver.quit()

def get_grafana_ids():
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-gpu')
	chrome_options.add_argument('--window-size=1920x1080')
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("http://" + db.ip_address[0] + ":" + GRAFANA_PORT + "/" + "login")
	time.sleep(10)
	driver.find_element("name","user").send_keys(GRAFANA_USERNAME)
	driver.find_element("name","password").send_keys(GRAFANA_PASSWORD)
	driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
	time.sleep(10)
	driver.get("http://"+db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest")
	time.sleep(10)
	attribute_name = "data-panelid"
	all_ids = driver.find_elements("xpath" , f"//*[@{attribute_name}]")
	ids=[]
	for i in all_ids:
		try:
			child_element = i.find_element("xpath",".//div[contains(@class, 'dashboard-row')]")
		except NoSuchElementException:
			ids.append(i)
	for id in ids:
		id = id.get_attribute("data-panelid")
		GRAFANA_DASH_IDS.append(int(id))
	print("GRAFANA DASH IDS : " , GRAFANA_DASH_IDS )
	print("Total panels : " , len(GRAFANA_DASH_IDS))
	print("--------------------------")
	return GRAFANA_DASH_IDS

if __name__ == '__main__':
    s_at = time.perf_counter()
    if os.path.exists(SCREENSHOT_DIR):shutil.rmtree(SCREENSHOT_DIR)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    grafana_ids = get_grafana_ids()			#Getting grafana ids
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(generate_grafana_trends, grafana_ids)   #should pass list of lists
    report = LoadTestReportNewPdf()
    report.create_pdf_from_images(SCREENSHOT_DIR,str(pdf_path), grafana_ids,table_ids)
    print('completed')