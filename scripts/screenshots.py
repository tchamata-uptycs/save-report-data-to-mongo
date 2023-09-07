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
from PIL import Image
import numpy as np
import io
import logging
logging.getLogger('seleniumwire').setLevel(logging.WARNING)
from  prometeus_utils import PrometheusConnector

executable_base_path = PrometheusConnector().base_stack_config_path
service = ChromeService(executable_path=f"{executable_base_path}/chromedriver")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')

class take_screenshots:
	def __init__(self,doc,start_time_str,dash_board_path ,prom_con_obj,elk_url, end_time_str,SCREENSHOT_DIR,start_margin=10,end_margin=10,panel_loading_time_threshold_sec=45,table_ids=[],thread_len = 10):
		format_data = "%Y-%m-%d %H:%M"
		start_time = datetime.strptime(start_time_str, format_data)
		end_time = datetime.strptime(end_time_str, format_data)
		start_time_epoch = int(start_time.timestamp() * 1000)
		end_time_epoch = int(end_time.timestamp() * 1000)
		
		if os.path.exists(SCREENSHOT_DIR):shutil.rmtree(SCREENSHOT_DIR)
		os.makedirs(SCREENSHOT_DIR, exist_ok=True)

		self.start_time_epoch = start_time_epoch
		self.end_time_epoch = end_time_epoch
		self.start_margin = start_margin
		self.end_margin = end_margin
		self.SCREENSHOT_DIR = SCREENSHOT_DIR
		self.panel_loading_time_threshold_sec=panel_loading_time_threshold_sec
		self.table_ids = table_ids
		self.thread_len = thread_len
		self.elk_url = elk_url
		self.db=prom_con_obj
		self.dash_board_path=dash_board_path
		self.monitoring_ip=prom_con_obj.monitoring_ip
		self.dash_board_url = "http://"+self.monitoring_ip+":"+self.db.GRAFANA_PORT+dash_board_path

		ist_timezone_offset = timedelta(hours=5, minutes=30)
		utc_starttime = start_time - ist_timezone_offset
		utc_endtime = end_time - ist_timezone_offset

		start_time_elk = utc_starttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
		end_time_elk = utc_endtime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
		self.compaction_status_url= f"http://{self.elk_url}:5601/app/dashboards#/view/Uptycs%20Data%20Pipeline?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:'{start_time_elk}',to:'{end_time_elk}'))"

	def generate_grafana_trends(self,l):
		driver = webdriver.Chrome(service=service,options=chrome_options)
		driver.get("http://" + self.monitoring_ip + ":" + self.db.GRAFANA_PORT + "/" + "login")

		driver.maximize_window()
		wait = WebDriverWait(driver, self.panel_loading_time_threshold_sec+60)  #waits for _ seconds
		try:
			wait.until(EC.visibility_of_element_located((By.NAME, "user"))).send_keys(self.db.GRAFANA_USERNAME)
		except Exception as e:
			print("Error: login page not loaded in time : ", type(e).__name__, "-", str(e))
		driver.find_element("name","password").send_keys(self.db.GRAFANA_PASSWORD)
		driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
		time.sleep(5)
		for t_id in l:
			if t_id in self.table_ids:
				ste = self.start_time_epoch
				ete = self.end_time_epoch
				url = (self.dash_board_url + "?orgId=1&from=%s&to=%s&viewPanel=%s") % (ste, ete, t_id)
			else:
				ste = self.start_time_epoch - (self.start_margin * (60 *1000))
				ete = self.end_time_epoch + (self.end_margin * (60 *1000))
				url = (self.dash_board_url+ "?orgId=1&from=%s&to=%s&viewPanel=%s&refresh=1s") % (ste, ete, t_id)
			driver.get(url)
			time.sleep(5)
			wait = WebDriverWait(driver, self.panel_loading_time_threshold_sec)  #waits for _ seconds
			try:
				title= wait.until(EC.visibility_of_element_located((By.XPATH, "//*/div[1]/header/div/h2"))).text
				screenshot = driver.get_screenshot_as_png()
				screenshot_image = Image.open(io.BytesIO(screenshot))
				average_pixel_value = np.mean(np.array(screenshot_image))
				if average_pixel_value < 84:
					title = f"LOADING FAILED : panel {t_id} not loaded in given time"
			except Exception as e:
				title = f"LOADING FAILED : panel {t_id} not loaded in given time"
			print(f"{title} : {t_id}")
			driver.save_screenshot(f'{self.SCREENSHOT_DIR}/{t_id}_1_{title}.png')
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
						driver.save_screenshot(f'{self.SCREENSHOT_DIR}/{t_id}_{page_number}_{title}.png')
						page_number += 1
						break
				if "active" in last_html:
					break
		driver.quit()

	def get_compaction_status(self):
		driver = webdriver.Chrome(service=service,options=chrome_options)
		driver.get(self.compaction_status_url)
		print(f"Connecting to : {self.compaction_status_url}")
		time.sleep(60)
		unique_number = int(time.time() * 1000)
		title="Compaction Status"
		print(f"{title} : {unique_number}")
		driver.save_screenshot(f'{self.SCREENSHOT_DIR}/{unique_number}_1_{title}.png')
		return unique_number

	def get_grafana_ids(self):
		driver = webdriver.Chrome(service=service,options = chrome_options)
		driver.get("http://" + self.monitoring_ip + ":" + self.db.GRAFANA_PORT + "/" + "login")
		print("Connecting to : http://" + self.monitoring_ip + ":" + self.db.GRAFANA_PORT + "/" + "login")

		wait = WebDriverWait(driver, self.panel_loading_time_threshold_sec+60)  #waits for _ seconds
		try:
			wait.until(EC.visibility_of_element_located((By.NAME, "user"))).send_keys(self.db.GRAFANA_USERNAME)
		except Exception as e:
			print(f"ERROR : Login page not loaded in time : {e}")
			print("Error:", type(e).__name__, "-", str(e))
		driver.find_element("name","password").send_keys(self.db.GRAFANA_PASSWORD)
		driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
		time.sleep(3)
		driver.get(self.dash_board_url)
		time.sleep(7)
		attribute_name = "data-panelid"
		all_ids = driver.find_elements("xpath" , f"//*[@{attribute_name}]")
		ids=[]
		for i in all_ids:
			try:
				child_element = i.find_element("xpath",".//div[contains(@class, 'dashboard-row')]")
			except NoSuchElementException:
				ids.append(i)
		grafana_ids = []
		for id in ids:
			id = id.get_attribute("data-panelid")
			grafana_ids.append(int(id))
		return grafana_ids

	def capture_screenshots_add_get_ids(self):
		grafana_ids = self.get_grafana_ids()
		temp_grafana_ids = grafana_ids[:]
		for tab in self.table_ids:
			if tab in temp_grafana_ids:temp_grafana_ids.remove(tab)
		FINAL = [temp_grafana_ids[i:i+self.thread_len] for i in range(0, len(temp_grafana_ids), self.thread_len)]

		for tab in self.table_ids:
			if tab in grafana_ids:
				FINAL.append([tab])
		print("Total number of grafana panels : " , len(grafana_ids))
		print('Grafana ids : ', FINAL)
		
		with concurrent.futures.ProcessPoolExecutor() as executor:
			executor.map(self.generate_grafana_trends, FINAL) 

		compaction_status_id = self.get_compaction_status()
		grafana_ids.append(compaction_status_id)

		return grafana_ids