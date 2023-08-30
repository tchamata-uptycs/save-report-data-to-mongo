from datetime import datetime, timedelta
from fpdf import FPDF
import os
from pathlib import Path
import prometeus_utils as prom
import time
from dateutil import tz
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.firefox.service import Service
from webdrivermanager import GeckoDriverManager
from selenium.webdriver.common.by import By
import shutil
from pdf2docx import Converter
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from copy import deepcopy
from selenium.common.exceptions import NoSuchElementException

start_time_str = '2023-07-26 21:55' 
end_time_str = '2023-07-27 09:55'
table_ids = [78 , 80 , 82] # table panel ids
start_margin = 15
end_margin = 50
FONT_SIZE = 15
FAILED_IDS = []

GRAFANA_USERNAME="admin"
GRAFANA_PASSWORD="admin123"
PROJECT_ROOT="/Users/masabathulararao/Documents/Loadtest"
GRAFANA_PORT = "3000"
SCREENSHOT_DIR="grafana_screenshots"
pdf_path =  PROJECT_ROOT / Path('results/recover_report.pdf')
output_path = PROJECT_ROOT / Path('results/report.docx')
GRAFANA_DASH_IDS = []

class LoadTestReport(FPDF):
    def __init__(
            self, font: str = 'Times', font_size: int = 12,desc_font: str = 'Arial', desc_font_size: int = 12,
            title: str = 'Load Test Report',start_time: datetime = datetime.utcnow(),
            end_time: datetime = datetime.utcnow() + timedelta(days=1),
            db: prom.PrometheusConnector = prom.PrometheusConnector('192.168.86.106', '9090')):
        super().__init__()
        self.title = title
        self.default_font = font 
        self.default_size = font_size
        self.desc_font = desc_font
        self.desc_font_size = desc_font_size
        self.start_time = start_time
        self.end_time = end_time
        self.db = db
        self.alias_nb_pages()
        self.add_page()
        self.set_font(font, 'B', font_size)


    def generate_grafana_trends(self,start_time: datetime = None,end_time: datetime = None,
                                load_type: str = "standard",event_rule_type: str = "javascript"):
        if not start_time: start_time = self.start_time
        if not end_time: end_time = self.end_time
        self.add_page()
        start_time_epoch = int(start_time.timestamp() * 1000)
        end_time_epoch = int(end_time.timestamp() * 1000)

        print(start_time_epoch,end_time_epoch)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=chrome_options)

        print("logging in ...")
        driver.get("http://" + self.db.ip_address[0] + ":" + GRAFANA_PORT + "/" + "login")
        driver.maximize_window()
        time.sleep(5)

        driver.find_element("name","user").send_keys(GRAFANA_USERNAME)
        driver.find_element("name","password").send_keys(GRAFANA_PASSWORD)
        driver.find_element("xpath","//*[@id='reactRoot']/div/main/div[3]/div/div[2]/div/div[1]/form/button/span").click()
        print("logged in successfully")
        time.sleep(5)
        driver.get("http://"+self.db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest")
        time.sleep(10)

        print(driver.current_url)        
        attribute_name = "data-panelid"
        all_ids = driver.find_elements("xpath" , f"//*[@{attribute_name}]")
        ids=[]
        for i in all_ids:
            try:
                child_element = i.find_element("xpath",".//div[contains(@class, 'dashboard-row')]")
            except NoSuchElementException:
                ids.append(i)

        print("FINAL ids length: " , len(ids) )



        for id in ids:
            id = id.get_attribute("data-panelid")
            GRAFANA_DASH_IDS.append(int(id))

        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        grafana_ids = deepcopy(GRAFANA_DASH_IDS)
        print("grafana_ids:", grafana_ids)
        print("Total panels : " , len(grafana_ids))
        print("--------------------------")


        for ind,i in enumerate(grafana_ids):

            try:
                if i in table_ids:
                    print("This is a table")
                    ste = start_time_epoch
                    ete = end_time_epoch
                    url = ("http://"+self.db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest?orgId=1&from=%s&to=%s&viewPanel=%s") % (ste, ete, i)
                else:
                    print("This is not a table")
                    ste = start_time_epoch - (start_margin * (60 *1000))
                    ete = end_time_epoch + (end_margin * (60 *1000))
                    url = ("http://"+self.db.ip_address[0]+":"+GRAFANA_PORT+"/d/0xQAxECVk/osqueryloadtest?orgId=1&from=%s&to=%s&viewPanel=%s&refresh=1s") % (ste, ete, i)
                driver.get(url)

                print("Count : " , ind+1)
                print("current panel_id : ",i)
                print("Current url : " , url)

                # time.sleep(10)
                wait = WebDriverWait(driver, 60000)

                print("wait started at : " , datetime.utcnow())
                title= wait.until(EC.visibility_of_element_located((By.XPATH, "//*/div[1]/header/div/h2"))).text
                print("wait ended at : " , datetime.utcnow())
                print("Panel title : ", title)  
                
                driver.save_screenshot(SCREENSHOT_DIR+"/%s.png" %title)

                # self.set_font("", 'B' )
                # self.set_font(font, 'B', font_size)

                self.cell(w=20, txt=title, align='l')
                self.ln(2)
                self.image((SCREENSHOT_DIR+"/%s.png" %title), h=100, w=190)
                self.ln(5)
                if (ind+1) % 2 == 0:self.add_page()
                print("added")
                print("----------------------------")

                count=0
                page_number = 2

                def filter(n):
                    l=[]
                    for i in n:
                        html = i.get_attribute("innerHTML")
                        if "table-panel-page-link" in html:
                            l.append(i)
                    return l

                while(True):
                    n = driver.find_elements(By.TAG_NAME, "li")
                    n= filter(n)
                    if len(n)==0:break
                    last_html = n[-1].get_attribute("innerHTML")
                    print("while loop")
                    active_flag = 0

                    for i in n:
                        print("iterating")
                        html = i.get_attribute("innerHTML")
                        if "active" in html:active_flag=1
                        if "active" not in html and active_flag==1:
                            print("inside")
                            print(html)
                            i.find_element(By.TAG_NAME , "a").click()
                            time.sleep(5)
                            driver.save_screenshot((SCREENSHOT_DIR+"/%s_%s.png") % (title , page_number))
                            # self.set_font("", 'B')
                            # self.set_font(font, 'B', font_size)
                            self.ln(2)
                            self.image(((SCREENSHOT_DIR+"/%s_%s.png") % (title , page_number)), h=100, w=190)
                            self.ln(5)
                            page_number += 1
                            count = count + 1
                            print(count)
                            if count % 2 == 0:self.add_page()
                            break
                    if "active" in last_html:
                        break
            except Exception as e:
                print(f"Failed for dashboard with id:{i} , ERROR : {e}")
                FAILED_IDS.append(i)


        driver.close()
        print("deleting screenshot folder")
        shutil.rmtree(SCREENSHOT_DIR)
        
if __name__ == '__main__':
    s_at = time.perf_counter()
    if os.path.exists(SCREENSHOT_DIR):shutil.rmtree(SCREENSHOT_DIR)

    format_data = "%Y-%m-%d %H:%M"
    # Parsing start_time_str and end_time_str to datetime objects
    start_time = datetime.strptime(start_time_str, format_data)
    end_time = datetime.strptime(end_time_str, format_data)
    report = LoadTestReport(start_time=start_time, end_time=end_time, db=prom.PrometheusConnector('s1monitor', '9090') , font_size=FONT_SIZE)
    report.generate_grafana_trends(start_time,end_time)
    print(pdf_path.resolve())
    report.output(pdf_path, 'F')

    f_at = time.perf_counter()
    print(f"Collecting the Screenshots took : {round(f_at - s_at,2)} seconds")
    print(f"Failed ids are  : {FAILED_IDS}")

    def convert_pdf_to_word(pdf_path, output_path):
        cv = Converter(pdf_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()

    convert_pdf_to_word(pdf_path, output_path)
