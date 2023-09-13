import requests
from datetime import datetime
import json
#-------------------------------------------------------------
HOST = 'Host'

memory_chart_queries = {f"{HOST}" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100) by (host_name)',
           'rule-engine' : "avg(uptycs_app_memory{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'osquery-ingestion' : "sum(uptycs_app_memory{app_name=~'osqueryIngestion'}) by (host_name)",
           "kafka" : "avg(uptycs_app_memory{app_name=~'kafka'}) by (host_name)",
           "trino" : "avg(uptycs_app_memory{app_name='trino'}) by (host_name)",
           "tls" : "avg(uptycs_app_memory{app_name='tls'}) by (host_name)",
           "eventsdb-ingestion" : "avg(uptycs_app_memory{app_name=~'eventsDbIngestion'}) by (host_name)",
           "logger" : "sum(uptycs_app_memory{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

cpu_chart_queries = {f"{HOST}" : 'avg(100-uptycs_idle_cpu) by (host_name)',
           'rule-engine' : "avg(uptycs_app_cpu{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'osquery-ingestion' : "avg(uptycs_app_cpu{app_name=~'osqueryIngestion'}) by (host_name)",
           "kafka" : "avg(uptycs_app_cpu{app_name=~'kafka'}) by (host_name)",
           "trino" : "avg(uptycs_app_cpu{app_name='trino'}) by (host_name)",
           "tls" : "avg(uptycs_app_cpu{app_name='tls'}) by (host_name)",
           "eventsdb-ingestion" : "avg(uptycs_app_cpu{app_name=~'eventsDbIngestion'}) by (host_name)",
           "logger" : "sum(uptycs_app_cpu{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }
lag_chart_queries={}
other_chart_queries={}

class Charts:
    def __init__(self,prom_con_obj,curr_ist_start_time,curr_ist_end_time,save_current_build_data_path):
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.save_current_build_data_path=save_current_build_data_path
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path

    def extract_charts_data(self,queries):
        final=dict()
        ist_time_format = '%Y-%m-%d %H:%M'
        start_time = (datetime.strptime(self.curr_ist_start_time, ist_time_format))
        end_time = (datetime.strptime(self.curr_ist_end_time, ist_time_format))
        stu = int(start_time.timestamp())
        etu = int(end_time.timestamp())

        for query in queries:
            PARAMS = {
                'query': queries[query],
                'start': stu,
                'end': etu,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            result = response.json()['data']['result']
            final[query] = result
        return final
            
    
    def capture_charts_and_save(self):
        memory_charts_data =  self.extract_charts_data(memory_chart_queries)
        cpu_charts_data =  self.extract_charts_data(cpu_chart_queries)
        lag_charts_data =  self.extract_charts_data(lag_chart_queries)
        other_charts_data =  self.extract_charts_data(other_chart_queries)
        
        with open(self.save_current_build_data_path, 'r') as file:
            current_build_data = json.load(file)
        current_build_data['charts']={
            "memory_charts_data":memory_charts_data,
            "cpu_charts_data":cpu_charts_data,
            "lag_charts_data":lag_charts_data,
            "other_charts_data":other_charts_data
        }
        with open(self.save_current_build_data_path, 'w') as file:
            json.dump(current_build_data, file, indent=4)  