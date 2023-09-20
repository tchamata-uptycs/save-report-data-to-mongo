from datetime import timedelta
import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from PIL import Image
import logging
logging.getLogger('seleniumwire').setLevel(logging.WARNING)
from  settings import configuration

executable_base_path = configuration().base_stack_config_path
service = ChromeService(executable_path=f"{executable_base_path}/chromedriver")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')

class take_screenshots:
    def __init__(self,start_time ,elk_url, end_time,fs):
        ist_timezone_offset = timedelta(hours=5, minutes=30)
        utc_starttime = start_time - ist_timezone_offset
        utc_endtime = end_time - ist_timezone_offset
        self.fs=fs
        start_time_elk = utc_starttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        end_time_elk = utc_endtime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.elk_url = elk_url
        self.compaction_status_url= f"http://{self.elk_url}:5601/app/dashboards#/view/4772c950-5771-11ee-95da-5780638a53fb?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:'{start_time_elk}',to:'{end_time_elk}'))"
    
    def get_compaction_status(self):
        driver = webdriver.Chrome(service=service,options=chrome_options)
        driver.get(self.compaction_status_url)
        print(f"Connecting to {self.compaction_status_url}")
        time.sleep(80)
        screenshot = driver.get_screenshot_as_png()
        try:
            with self.fs.new_file(filename="screenshot.png") as fp:
                fp.write(screenshot)
                screenshot_id = fp._id
            print("compaction status screenshot captured with file _id:", screenshot_id)
        except:
            print(f"ERROR : failed to save conpaction status to mongo")
            screenshot_id=None
        return {"compaction_status_chart":screenshot_id}