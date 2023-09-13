import requests
from datetime import datetime
import json
#-------------------------------------------------------------
HOST = 'Host'
memory_tag = "Memory"
cpu_tag = "CPU"
memory_unit = "GB"
cpu_unit = "cores"

memory_queries = {f"{HOST}" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100) by (host_name)',
           'rule-engine' : "avg(uptycs_app_memory{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'osquery-ingestion' : "sum(uptycs_app_memory{app_name=~'osqueryIngestion'}) by (host_name)",
           "kafka" : "avg(uptycs_app_memory{app_name=~'kafka'}) by (host_name)",
           "trino" : "avg(uptycs_app_memory{app_name='trino'}) by (host_name)",
           "tls" : "avg(uptycs_app_memory{app_name='tls'}) by (host_name)",
           "eventsdb-ingestion" : "avg(uptycs_app_memory{app_name=~'eventsDbIngestion'}) by (host_name)",
           "logger" : "sum(uptycs_app_memory{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

cpu_queries = {f"{HOST}" : 'avg(100-uptycs_idle_cpu) by (host_name)',
           'rule-engine' : "avg(uptycs_app_cpu{app_name=~'.*ruleEngine.*'}) by (host_name)",
           'osquery-ingestion' : "avg(uptycs_app_cpu{app_name=~'osqueryIngestion'}) by (host_name)",
           "kafka" : "avg(uptycs_app_cpu{app_name=~'kafka'}) by (host_name)",
           "trino" : "avg(uptycs_app_cpu{app_name='trino'}) by (host_name)",
           "tls" : "avg(uptycs_app_cpu{app_name='tls'}) by (host_name)",
           "eventsdb-ingestion" : "avg(uptycs_app_cpu{app_name=~'eventsDbIngestion'}) by (host_name)",
           "logger" : "sum(uptycs_app_cpu{app_name=~'.*osqLogger-1.*'}) by (host_name)"
           }

container_memory_queries = {'container' : "sum(uptycs_docker_mem_used{}/(1000*1000*1000)) by (container_name)",}
container_cpu_queries = {'container' : "sum(uptycs_docker_cpu_stats{}) by (container_name)",}

class MC_comparisions:
    def __init__(self,prom_con_obj,curr_ist_start_time,curr_ist_end_time):
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.test_env_file_path=prom_con_obj.test_env_file_path
        with open(self.test_env_file_path, 'r') as file:
            self.nodes_data = json.load(file)

    def extract_data(self,queries,tag,unit):
        final=dict()
        return_overall = dict()
        ist_time_format = '%Y-%m-%d %H:%M'
        start_time = (datetime.strptime(self.curr_ist_start_time, ist_time_format))
        end_time = (datetime.strptime(self.curr_ist_end_time, ist_time_format))
        stu = int(start_time.timestamp())
        etu = int(end_time.timestamp())

        for query in queries:
            final[query] = {}
            PARAMS = {
                'query': queries[query],
                'start': stu,
                'end': etu,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            result = response.json()['data']['result']
            for res in result:
                hostname = res['metric']['host_name']
                if str(hostname).endswith('v') and len(hostname)>1:
                    hostname = str(hostname)[:-1]
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                minimum = min(values)
                maximum = max(values)
                final[query][hostname] = {"percentage":{"average":avg , "minimum":minimum , "maximum":maximum}}
                final[query][hostname][unit]={}
                if tag == memory_tag:
                    final[query][hostname][unit]={
                        'average':avg * float(self.nodes_data[hostname]['ram']) / 100,
                        'minimum':minimum * float(self.nodes_data[hostname]['ram']) / 100,
                        'maximum':maximum * float(self.nodes_data[hostname]['ram']) / 100
                    }
                else:
                    if query == HOST:
                        final[query][hostname][unit]={
                            'average':avg * float(self.nodes_data[hostname]['cores']) / 100,
                            'minimum':minimum * float(self.nodes_data[hostname]['cores']) / 100,
                            'maximum':maximum * float(self.nodes_data[hostname]['cores']) / 100
                        }
                    else:
                        final[query][hostname][unit]={
                            'average':avg/100,
                            'minimum': minimum/100,
                            'maximum': maximum/100
                        }

        #calculate overall pnodes,dnodes,pgnodes usage
        new_data = final[HOST]
        for node_type in ["pnodes" , "dnodes" , "pgnodes"]:
            new_sum=0
            for node in self.nodes_data[node_type]:
                new_sum+=new_data[node][unit]["average"]
            return_overall[node_type] = {f"{unit}":new_sum}
        return final,return_overall

    def extract_container_data(self,queries,tag,unit):
        final=dict()
        ist_time_format = '%Y-%m-%d %H:%M'
        start_time_utc = (datetime.strptime(self.curr_ist_start_time, ist_time_format))
        end_time_utc = (datetime.strptime(self.curr_ist_end_time, ist_time_format))
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
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            result = response.json()['data']['result']
            for res in result:
                container_name = res['metric']['container_name']
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                minimum = min(values)
                maximum = max(values)
                if tag == cpu_tag:
                    avg = avg/100
                    minimum = minimum/100
                    maximum = maximum/100
                final[query][container_name] = {f"{unit}":{"average":avg , "minimum":minimum , "maximum":maximum}}
        return final 
    
    def make_comparisions(self):
        memory_data,overall_memory_data = self.extract_data(memory_queries,memory_tag,memory_unit)
        cpu_data,overall_cpu_data = self.extract_data(cpu_queries,cpu_tag,cpu_unit)
        container_memory_data =  self.extract_container_data(container_memory_queries,memory_tag,memory_unit)
        container_cpu_data =  self.extract_container_data(container_cpu_queries,cpu_tag,cpu_unit)
        
        current_build_data={}
        current_build_data["overall_nodes_average_memory_usage"]=overall_memory_data
        current_build_data["overall_nodes_average_cpu_usage"]=overall_cpu_data
        current_build_data["node_level_average_memory_usage"]=memory_data
        current_build_data["node_level_average_cpu_usage"]=cpu_data
        current_build_data["container_level_average_memory_usage"] = container_memory_data
        current_build_data["container_level_average_cpu_usage"] = container_cpu_data
        return current_build_data