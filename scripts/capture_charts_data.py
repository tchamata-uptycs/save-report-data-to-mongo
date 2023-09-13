import requests
from datetime import datetime
import json

memory_chart_queries = {f"Host" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100) by (host_name)',
           'rule-engine' : "avg(uptycs_app_memory{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'osquery-ingestion' : "sum(uptycs_app_memory{app_name=~'osqueryIngestion'}) by (host_name)",
           "kafka" : "avg(uptycs_app_memory{app_name=~'kafka'}) by (host_name)",
           "trino" : "avg(uptycs_app_memory{app_name='trino'}) by (host_name)",
           "tls" : "avg(uptycs_app_memory{app_name='tls'}) by (host_name)",
           "eventsdb-ingestion" : "avg(uptycs_app_memory{app_name=~'eventsDbIngestion'}) by (host_name)",
           "logger" : "sum(uptycs_app_memory{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

cpu_chart_queries = {f"Host" : 'avg(100-uptycs_idle_cpu) by (host_name)',
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
    def __init__(self,prom_con_obj,curr_ist_start_time,curr_ist_end_time,add_extra_time_for_charts_at_end_in_min):
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.add_extra_time_for_charts_at_end_in_min=add_extra_time_for_charts_at_end_in_min
        self.add_extra_time_for_charts_at_start_in_min=10

    def extract_charts_data(self,queries):
        final=dict()
        ist_time_format = '%Y-%m-%d %H:%M'
        start_time = (datetime.strptime(self.curr_ist_start_time, ist_time_format))
        end_time = (datetime.strptime(self.curr_ist_end_time, ist_time_format))
        stu = int(start_time.timestamp())
        etu = int(end_time.timestamp())
        ste = stu - (self.add_extra_time_for_charts_at_start_in_min * (60))
        ete = etu + (self.add_extra_time_for_charts_at_end_in_min * (60))

        for query in queries:
            PARAMS = {
                'query': queries[query],
                'start': ste,
                'end': ete,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            result = response.json()['data']['result']
            final[query] = result
        return final
            
    def capture_charts_and_save(self): 
        return {
            "memory_charts_data":self.extract_charts_data(memory_chart_queries),
            "cpu_charts_data":self.extract_charts_data(cpu_chart_queries),
            "lag_charts_data":self.extract_charts_data(lag_chart_queries),
            "other_charts_data":self.extract_charts_data(other_chart_queries)
        }