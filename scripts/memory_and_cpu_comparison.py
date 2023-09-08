import requests
from datetime import datetime
import json
from docx import Document
from collections import defaultdict

#-------------------------------------------------------------
HOST = 'Host'
memory_tag = "Memory"
cpu_tag = "CPU"
memory_unit = "GB"
cpu_unit = "cores"

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

container_memory_queries = {'Container' : "sum(uptycs_docker_mem_used{}/(1000*1000*1000)) by (container_name)",}
container_cpu_queries = {'Container' : "sum(uptycs_docker_cpu_stats{}) by (container_name)",}

class MC_comparisions:
    def __init__(self,prom_con_obj,curr_ist_start_time,curr_ist_end_time,save_current_build_data_path,show_gb_cores=True):
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.show_gb_cores=show_gb_cores
        self.save_current_build_data_path=save_current_build_data_path

        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path

        self.test_env_file_path=prom_con_obj.test_env_file_path
        self.complete_usage = defaultdict(lambda : 0)
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
                final[query][hostname] = {"percentage":avg}
                if tag == memory_tag:
                    final[query][hostname][unit] = avg * float(self.nodes_data[hostname]['ram']) / 100
                else:
                    if query == HOST:
                        final[query][hostname][unit] = avg * float(self.nodes_data[hostname]['cores']) / 100
                    else:
                        final[query][hostname][unit] = avg/100

        #calculate overall pnodes,dnodes,pgnodes usage
        new_data = final[HOST]
        
        for node_type in ["pnodes" , "dnodes" , "pgnodes"]:
            new_sum=0
            for node in self.nodes_data[node_type]:
                new_sum+=new_data[node][unit]
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
                
                hostname = res['metric']['container_name']
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                if tag == memory_tag:
                    final[query][hostname] = {f"{unit}":avg}
                    self.complete_usage[tag]+=avg
                else:
                    final[query][hostname] = {f"{unit}":avg/100}
                    self.complete_usage[tag]+=avg/100

        return final 

    def get_summary_dict(self):
        final=[]
        for tag in self.summary:
            unit = self.summary[tag]["unit"]
            for inc_or_dec in self.summary[tag]["increased_or_decreased"]:
                data_dict=dict()
                individual_summary = dict(sorted(self.summary[tag]["increased_or_decreased"][inc_or_dec].items(), key=lambda item: item[1][0], reverse=True))
                data_dict["title"] = f'{tag} usage {inc_or_dec} summary'
                data_dict["header"] = [ "Metric",f'{inc_or_dec} in {unit}' , "Relative val(%)" ]
                data_dict["body"] = []
                for metric in individual_summary:
                    curr_list=[]
                    if metric == "TOTAL":
                        individual_summary[metric][0]=abs(individual_summary[metric][0])
                    curr_list.append((metric))
                    if inc_or_dec == "increased":
                        curr_list.append((f"{individual_summary[metric][0]:.2f}", "red"))
                        curr_list.append((f"{individual_summary[metric][1]:.2f}" , "red"))
                    else:
                        curr_list.append((f"{individual_summary[metric][0]:.2f}" ,  "green"))
                        curr_list.append((f"{individual_summary[metric][1]:.2f}" , "green"))
                    data_dict["body"].append(curr_list)
                final.append(data_dict)
        return final

    def make_comparisions(self):
        memory_data =  {'tag':memory_tag,'unit':memory_unit}
        cpu_data   =   {'tag':cpu_tag,"unit":cpu_unit}
        
        memory_data["current"] , memory_data["overall_current"] = self.extract_data(memory_queries,memory_tag,memory_unit)
        cpu_data["current"] , cpu_data["overall_current"] = self.extract_data(cpu_queries,cpu_tag,cpu_unit)
        
        container_memory_data = {'current' : self.extract_container_data(container_memory_queries,memory_tag,memory_unit),
                                'tag':memory_tag,
                                'unit':memory_unit}

        container_cpu_data = {'current' : self.extract_container_data(container_cpu_queries,cpu_tag,cpu_unit),
                            'tag':cpu_tag,
                            "unit":cpu_unit}
        
        with open(self.save_current_build_data_path, 'r') as file:
            current_build_data = json.load(file)

        current_build_data["overall_memory"]=memory_data["overall_current"]
        current_build_data["overall_cpu"]=cpu_data["overall_current"]
        current_build_data["memory"]=memory_data["current"]
        current_build_data["cpu"]=cpu_data["current"]
        current_build_data["container_wise_memory"] = container_memory_data["current"]
        current_build_data["container_wise_cpu"] = container_cpu_data["current"]
        current_build_data["complete_usage"] = self.complete_usage

        with open(self.save_current_build_data_path, 'w') as file:
            json.dump(current_build_data, file, indent=4)  # indent for pretty formatting