import requests
from datetime import datetime, timedelta
import json
from docx import Document
from docx.shared import RGBColor
from pathlib import Path
import os
from collections import defaultdict
from helper import add_table,excel_update

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


container_memory_queries = {
           'Container' : "sum(uptycs_docker_mem_used{}/(1000*1000*1000)) by (container_name)",
          }

container_cpu_queries = {
           'Container' : "sum(uptycs_docker_cpu_stats{}) by (container_name)",
           }
class MC_comparisions:
    def __init__(self,sprint,prom_con_obj,build,load_type,doc,curr_ist_start_time,curr_ist_end_time,save_current_build_data_path,fetch_prev_build_data_path,overall_comparisions_docx_path,previous_excel_file_path,current_excel_file_path,show_gb_cores=True):
        self.doc = doc
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.show_gb_cores=show_gb_cores
        self.fetch_prev_build_data_path=fetch_prev_build_data_path
        self.save_current_build_data_path=save_current_build_data_path

        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path

        self.nodes_file_path=prom_con_obj.nodes_file_path
        self.sprint=sprint
        self.build = build
        self.load_type = load_type
        self.prev_build = '-'
        self.overall_comparisions_docx_path=overall_comparisions_docx_path
        self.previous_excel_file_path=previous_excel_file_path
        self.current_excel_file_path=current_excel_file_path

        self.complete_usage = defaultdict(lambda : 0)
        with open(self.nodes_file_path, 'r') as file:
            self.nodes_data = json.load(file)

        self.summary={  memory_tag:{"increased_or_decreased" :{
                                        "increased":{"TOTAL" : [0,0]} ,
                                        "decreased":{"TOTAL" : [0,0]}
                                        },
                                    "unit":memory_unit,
                                },
                        cpu_tag:    {"increased_or_decreased" :{
                                        "increased":{"TOTAL" : [0,0]} ,
                                        "decreased":{"TOTAL" : [0,0]}
                                    },
                                "unit":cpu_unit,
                            }
                    }

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
                    if hostname in self.nodes_data:
                        final[query][hostname][unit] = avg * float(self.nodes_data[hostname]['ram']) / 100
                    else:
                        final[query][hostname][unit] = None
                else:
                    if query == HOST:
                        if hostname in self.nodes_data:
                            final[query][hostname][unit] = avg * float(self.nodes_data[hostname]['cores']) / 100
                        else:
                            final[query][hostname][unit] = None
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
                # print(f"{query} : {hostname}")
                if tag == memory_tag:
                    final[query][hostname] = {f"{unit}":avg}
                    self.complete_usage[tag]+=avg
                else:
                    final[query][hostname] = {f"{unit}":avg/100}
                    self.complete_usage[tag]+=avg/100

        return final 
    
    def get_complete_container_utilization(self,data):

        data_dict=dict()
        old_data = data['previous']
        new_data = data['current']
        data_dict["title"] = f"Complete resource usage(GB/cores)"
        data_dict["header"] = [ "Metric",self.prev_build,self.build, "Absolute(%)" , "Relative(%)" ]
        data_dict["body"] = []

        for tag in new_data:
            curr_list=[]
            curr_list.append((f"Complete {tag} usage",'-'))
            try:
                
                curr_list.append((f"{old_data[tag]:.2f}" , round(old_data[tag], 2)))
            except:
                curr_list.append(('-' , '-'))            
            curr_list.append((f"{new_data[tag]:.2f}" , round(new_data[tag], 2)))
            try:
                diff = round(old_data[tag]-new_data[tag] , 2)
                relative = round((old_data[tag]-new_data[tag]) / old_data[tag] , 2)
                if diff >0:
                    curr_list.append((str(abs(diff)) + " ⬇️" , abs(diff), "green"))
                    curr_list.append((str(abs(relative)) + " ⬇️" ,abs(relative), "green"))
                elif diff < 0 :
                    curr_list.append((str(abs(diff)) + " ⬆️" ,abs(diff), "red"))
                    curr_list.append((str(abs(relative)) + " ⬆️" ,abs(relative), "red"))
                else:
                    curr_list.append((str(abs(diff)) , abs(diff)))
                    curr_list.append((str(abs(relative)) , abs(relative)))

            except:
                curr_list.append(('-','-'))
                curr_list.append(('-','-'))

            data_dict['body'].append(curr_list)
        return data_dict



    def get_container_utilization(self,data):
        data_dict=dict()
        data_dict["header"] = [ "Metric",self.prev_build,self.build, "Absolute(%)" , "Relative(%)" ]
        data_dict["body"] = []
        old_data = data['previous']
        new_data = data['current']
        tag = data['tag']
        unit = data['unit']
        data_dict["title"] = f"Overall Container {tag} usages"
        for query in new_data:
            for host_name in new_data[query]:
                curr_list = []
                curr_list.append((f"{tag} used by container {host_name}",'-'))
                text = f"{tag} by {host_name}"
                try : 
                    curr_list.append((f"{old_data[query][host_name][unit]:.2f} {unit}" ,round(old_data[query][host_name][unit],2) ))
                    diff = float(old_data[query][host_name][unit]) - float(new_data[query][host_name][unit])
                    relative = float(((old_data[query][host_name][unit]) - float(new_data[query][host_name][unit]))*100 / old_data[query][host_name][unit])
                except Exception as e:
                    print("Error:", type(e).__name__, "-", str(e))
                    curr_list.append(('-' , '-'))
                    diff = - float(new_data[query][host_name][unit])
                    relative=0
                    
                curr_list.append((f"{new_data[query][host_name][unit]:.2f} {unit}" , round(new_data[query][host_name][unit],2)))

                difference_text = f"{abs(diff):.2f} {unit}"
                relative_text = f"{abs(relative):.2f} %"


                if diff<0:
                    curr_list.append((difference_text + " ⬆️" ,round(abs(diff),2), "red"))
                    curr_list.append((relative_text + " ⬆️" ,round(abs(relative),2), "red"))
                    # run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                    # run2.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                    self.summary[tag]["increased_or_decreased"]["increased"]["TOTAL"][0] -= abs(diff)

                    if abs(diff)>1 or abs(relative) > 10:
                        self.summary[tag]["increased_or_decreased"]["increased"][text] = [abs(diff),abs(relative)]

                elif diff >0:
                    curr_list.append((difference_text + " ⬇️" ,round(abs(diff),2), "green"))
                    curr_list.append((relative_text + " ⬇️" ,round(abs(relative),2), "green"))
                    # run.font.color.rgb = RGBColor(0, 128, 0)  # Green color
                    # run2.font.color.rgb = RGBColor(0, 128, 0)  # Green color
                    self.summary[tag]["increased_or_decreased"]["decreased"]["TOTAL"][0] -= abs(diff)
                    if abs(diff)>1 or abs(relative) > 10:
                        self.summary[tag]["increased_or_decreased"]["decreased"][text] = [abs(diff) , abs(relative)]

                else:
                    curr_list.append((difference_text , round(abs(diff),2)))
                    curr_list.append((relative_text , round(abs(relative),2)))
                data_dict["body"].append(curr_list)
        return data_dict

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
                    curr_list.append((metric,metric))
                    if inc_or_dec == "increased":
                        curr_list.append((f"{individual_summary[metric][0]:.2f}" , round(individual_summary[metric][0],2) , "red"))
                        curr_list.append((f"{individual_summary[metric][1]:.2f}" , round(individual_summary[metric][1],2) , "red"))
                    else:
                        curr_list.append((f"{individual_summary[metric][0]:.2f}" , round(individual_summary[metric][0],2) ,  "green"))
                        curr_list.append((f"{individual_summary[metric][1]:.2f}" ,  round(individual_summary[metric][1],2) , "green"))
                    data_dict["body"].append(curr_list)
                final.append(data_dict)
        return final

    def get_average_utilization(self,data):
        data_dict=dict()
        data_dict["header"] = [ "Metric",self.prev_build,self.build, "Absolute(%)" , "Relative(%)" ]
        data_dict["body"] = []
        old_data = data['previous']
        new_data = data['current']
        tag = data['tag']
        unit = data['unit']
        data_dict["title"] = f"Comparision of Average {tag} utilization"

        for query in new_data:
            for host_name in new_data[query]:
                curr_list = []
                if query==HOST:
                    curr_list.append((f"{tag} used by {host_name}" , '-'))
                else:
                    curr_list.append((f"{tag} used by {query} {host_name}" , '-'))
                try : 
                    if old_data[query][host_name][unit] :
                        _=f"{old_data[query][host_name]['percentage']:.2f}% ({old_data[query][host_name][unit]:.2f} {unit})"
                    else:
                        _ = f"{old_data[query][host_name]['percentage']:.2f}%"
                    
                    if old_data[query][host_name][unit] and self.show_gb_cores:
                        a=f" {old_data[query][host_name]['percentage']:.2f}% ({old_data[query][host_name][unit]:.2f} {unit})"
                        curr_list.append((a,a))
                    else:
                        b=f"{old_data[query][host_name]['percentage']:.2f}%"
                        curr_list.append((b,_))
                    
                except Exception as e:
                    curr_list.append(('-' , '-'))
                    print("Error:", type(e).__name__, "-", str(e))

                if new_data[query][host_name][unit]:
                    __=f"{new_data[query][host_name]['percentage']:.2f}% ({new_data[query][host_name][unit]:.2f} {unit})"
                else:
                    __=f"{new_data[query][host_name]['percentage']:.2f}%"

                if new_data[query][host_name][unit] and self.show_gb_cores:
                    c=f"{new_data[query][host_name]['percentage']:.2f}% ({new_data[query][host_name][unit]:.2f} {unit})"
                    curr_list.append((c,c))
                
                else:
                    d=f"{new_data[query][host_name]['percentage']:.2f}%"
                    curr_list.append((d,__))

                try : 
                    sign = None
                    percent_diff = float(old_data[query][host_name]['percentage']) - float(new_data[query][host_name]['percentage'])
                    if old_data[query][host_name][unit] and new_data[query][host_name][unit]:
                        diff = float(old_data[query][host_name][unit]) - float(new_data[query][host_name][unit])
                        row4_text = f"{abs(diff) *100  / (float(old_data[query][host_name][unit])) :.2f} %"

                        __diff = f"{abs(diff):.2f} {unit} ({abs(percent_diff):.2f}%)"

                        if self.show_gb_cores:
                            difference_text = f"{abs(diff):.2f} {unit} ({abs(percent_diff):.2f}%)"
                        else:
                            difference_text = f"{abs(percent_diff):.2f}%"
                        sign = diff
                    else:
                        row4_text = f"{abs(percent_diff) *100  / (float(old_data[query][host_name]['percentage'])) :.2f} %"
                        difference_text = f"{abs(percent_diff):.2f}%"
                        sign = percent_diff
                        __diff = difference_text
                        __diff = float(__diff[:-1])

                    __rel = float(row4_text[:-1])
                    
                    if sign<0:
                        curr_list.append((difference_text + " ⬆️" ,__diff  , "red"))
                        curr_list.append((row4_text+ " ⬆️" ,__rel , "red"))
                    elif sign>0:
                        curr_list.append((difference_text + " ⬇️" ,__diff ,"green"))
                        curr_list.append((row4_text + " ⬇️",__rel , "green"))
                    else:
                        curr_list.append((difference_text,__diff))
                        curr_list.append((row4_text,__rel))

                except Exception as e:
                    print(" --- WHAT IS THE ERROR ----")
                    print("Error:", type(e).__name__, "-", str(e))
                    curr_list.append(('-' , '-'))
                    curr_list.append(('-' , '-'))

                data_dict["body"].append(curr_list)

        return data_dict


    def get_overall_utilization(self,data):
        data_dict=dict()
        data_dict["header"] = [ "Metric",self.prev_build,self.build, "Delta" ]
        data_dict["body"] = []
        old_data = data['overall_previous']
        new_data = data['overall_current']
        tag = data['tag']
        unit = data['unit']
        data_dict["title"] = f"Comparision of Overall {tag} utilization"

        for node_type in new_data:
            curr_list=[]
            curr_list.append((f"Average {tag} used by {node_type}" , '-'))
            try:
                curr_list.append((f"{old_data[node_type][unit]:.2f} {unit}" , round(old_data[node_type][unit],2)))
            except:
                curr_list.append(('-','-'))
            curr_list.append((f"{new_data[node_type][unit]:.2f} {unit}" , round(new_data[node_type][unit],2)))
            try:
                diff = old_data[node_type][unit]-new_data[node_type][unit]
                difference_text = f"{abs(diff *100/ old_data[node_type][unit]):.2f}% ({abs(diff):.2f} {unit})"
                if diff<0:
                    curr_list.append((difference_text + " ⬆️" ,difference_text, "red"))
                elif diff>0:
                    curr_list.append((difference_text + " ⬇️" , difference_text,"green"))
                else:
                    curr_list.append((difference_text,difference_text))
            except Exception as e:
                print("Error:", type(e).__name__, "-", str(e))
                curr_list.append(('-','-'))
            data_dict["body"].append(curr_list)
        return data_dict

        
    def make_comparisions(self):
        past_file_exists=False
        if os.path.exists(self.fetch_prev_build_data_path):
            with open(self.fetch_prev_build_data_path, 'r') as file:
                previous_build_data = json.load(file)
            past_file_exists=True
            self.prev_build = previous_build_data["details"]["build"]
        else:
            previous_build_data={}
        previous_build_data = defaultdict(lambda : 0, previous_build_data)
        print("Extracting current build data ...")

        memory_data =  {'previous' : previous_build_data["memory"],
                        'overall_previous' :previous_build_data["overall_memory"],
                        'tag':memory_tag,
                        'unit':memory_unit}

        cpu_data   =   {'previous' : previous_build_data["cpu"],
                        'overall_previous' :previous_build_data["overall_cpu"],
                        'tag':cpu_tag,
                        "unit":cpu_unit}
        
        memory_data["current"] , memory_data["overall_current"] = self.extract_data(memory_queries,memory_tag,memory_unit)
        cpu_data["current"] , cpu_data["overall_current"] = self.extract_data(cpu_queries,cpu_tag,cpu_unit)
        
        container_memory_data = { 'previous' : previous_build_data["container_wise_memory"],
                                'current' : self.extract_container_data(container_memory_queries,memory_tag,memory_unit),
                                'tag':memory_tag,
                                'unit':memory_unit}

        container_cpu_data = {'previous' : previous_build_data["container_wise_cpu"],
                            'current' : self.extract_container_data(container_cpu_queries,cpu_tag,cpu_unit),
                            'tag':cpu_tag,
                            "unit":cpu_unit}
        
        container_complete_usage = {
            'previous':previous_build_data["complete_usage"],
            "current" : self.complete_usage
        }
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


        sheets = {
                "memory trend":self.get_average_utilization(memory_data),
                  "cpu trend":self.get_average_utilization(cpu_data),
                  "container-wise memory trend":self.get_container_utilization(container_memory_data),
                  "container-wise cpu trend":self.get_container_utilization(container_cpu_data),
                  "overall mem":self.get_overall_utilization(memory_data),
                  "overall cpu":self.get_overall_utilization(cpu_data),
                  "complete usage":self.get_complete_container_utilization(container_complete_usage),
                  }
        
        self.doc.add_heading('Average Resource Utilization', level=2)
        self.doc=add_table(self.doc,    sheets["memory trend"])
        self.doc=add_table(self.doc,    sheets["cpu trend"])

        self.doc.add_heading('Overall Usages', level=2)
        self.doc=add_table(self.doc,    sheets["overall mem"])
        self.doc=add_table(self.doc,    sheets["overall cpu"])

        #---- container wise -----------
        self.container_doc = Document()
        self.container_doc.add_heading('Container-wise Resource Usage Report', level=0)

        self.container_doc = add_table(self.container_doc , sheets["container-wise memory trend"])
        self.container_doc = add_table(self.container_doc , sheets["container-wise memory trend"])
        if past_file_exists:
            self.container_doc.add_heading(f'Usage Increase/decrease Summary', level=2)
            for table in self.get_summary_dict():
                self.container_doc = add_table(self.container_doc , table)

        self.container_doc = add_table(self.container_doc , sheets["complete usage"])
        self.container_doc.save(self.overall_comparisions_docx_path)
        #-------------------------------

        #update excel
        excel_update(sheets , self.previous_excel_file_path ,self.current_excel_file_path , build = self.build)
        return self.doc
