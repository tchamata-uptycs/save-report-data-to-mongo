import requests
from datetime import datetime, timedelta
import json
from docx import Document
from docx.shared import RGBColor
from pathlib import Path
import os

PROMETHEUS = "http://192.168.128.50:9090"
API_PATH = '/api/v1/query_range'

#-------------------------get for only a time range and save it-------------------------------------
curr_ist_start_time = '2023-08-02 15:56' 
curr_ist_end_time = '2023-08-02 20:56'
sprint = "136"
build = "136020"
load_type = "SingleCustomer"
#-------------------------------------------------------------
comparisions_docx_path = Path(f'generated_reports/{sprint}/{load_type}/{build}_{load_type}_comparisions.docx')
os.makedirs(os.path.dirname(comparisions_docx_path), exist_ok=True)
save_current_build_data_path = Path(f'generated_reports/{sprint}/{load_type}/mem_cpu_comparision_data.json')

HOST = 'Host'
memory_tag = "Memory"
cpu_tag = "CPU"
memory_unit = "GB"
cpu_unit = "cores"
description = "This data is the memory and cpu usages of each host and for each container in a host"

memory_queries = {f"{HOST}" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100) by (host_name)',
           'Rule Engine' : "avg(uptycs_app_memory{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'Osquery Ingestion' : "sum(uptycs_app_memory{app_name=~'osqueryIngestion'}) by (host_name)",
           "Kafka" : "avg(uptycs_app_memory{app_name=~'kafka'}) by (host_name)",
           "Trino" : "avg(uptycs_app_memory{app_name='trino'}) by (host_name)",
           "Tls" : "avg(uptycs_app_memory{app_name='tls'}) by (host_name)",
           "EventsDbIngestion" : "avg(uptycs_app_memory{app_name=~'eventsDbIngestion'}) by (host_name)",
           "Logger" : "sum(uptycs_app_memory{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

cpu_queries = {f"{HOST}" : 'avg(100-uptycs_idle_cpu) by (host_name)',
           'Rule Engine' : "avg(uptycs_app_cpu{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'Osquery Ingestion' : "avg(uptycs_app_cpu{app_name=~'osqueryIngestion'}) by (host_name)",
           "Kafka" : "avg(uptycs_app_cpu{app_name=~'kafka'}) by (host_name)",
           "Trino" : "avg(uptycs_app_cpu{app_name='trino'}) by (host_name)",
           "Tls" : "avg(uptycs_app_cpu{app_name='tls'}) by (host_name)",
           "EventsDbIngestion" : "avg(uptycs_app_cpu{app_name=~'eventsDbIngestion'}) by (host_name)",
           "Logger" : "sum(uptycs_app_cpu{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

nodes_file_path = 's1_nodes.json'
with open(nodes_file_path, 'r') as file:
    nodes_data = json.load(file)

def extract_data(queries,ist_start_time,ist_end_time,tag):
    final=dict()
    ist_time_format = '%Y-%m-%d %H:%M'
    start_time_utc = (datetime.strptime(ist_start_time, ist_time_format))
    end_time_utc = (datetime.strptime(ist_end_time, ist_time_format))
    stu = int(start_time_utc.timestamp())
    etu = int(end_time_utc.timestamp())
    for query in queries:
        final[query] = {}
        PARAMS = {
            'query': queries[query],
            'start': stu,
            'end': etu,
            'step':15
        }
        response = requests.get(PROMETHEUS + API_PATH, params=PARAMS)
        result = response.json()['data']['result']
        if tag == memory_tag:
            for res in result:
                hostname = res['metric']['host_name']
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                final[query][hostname] = {"percentage":avg}
                if hostname in nodes_data:
                    final[query][hostname][memory_unit] = avg * float(nodes_data[hostname]['ram']) / 100
                else:
                    final[query][hostname][memory_unit] = None
        else:
            for res in result:
                hostname = res['metric']['host_name']
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                final[query][hostname] = {"percentage":avg}
                if query == HOST:
                    if hostname in nodes_data:
                        final[query][hostname][cpu_unit] = avg * float(nodes_data[hostname]['cores']) / 100
                    else:
                        final[query][hostname][cpu_unit] = None
                else:
                    final[query][hostname][cpu_unit] = avg/100
    return final

memory_data = {
               'current' : extract_data(memory_queries,curr_ist_start_time,curr_ist_end_time,memory_tag),
             }

cpu_data = {
               'current' : extract_data(cpu_queries,curr_ist_start_time,curr_ist_end_time,cpu_tag),
            }

current_build_data = {
    "details": {
		"sprint": f"{sprint}",
		"build": f"{build}",
		"load_type":f"{load_type}",
        "description" : f"{description}",
        "load_start_time_ist" : f"{curr_ist_start_time}",
        "load_end_time_ist" : f"{curr_ist_end_time}"
	},
    "memory":memory_data["current"],
    "cpu":cpu_data["current"]}

with open(save_current_build_data_path, 'w') as file:
    json.dump(current_build_data, file, indent=4)  # indent for pretty formatting

print("saved current build data to : ",save_current_build_data_path)
