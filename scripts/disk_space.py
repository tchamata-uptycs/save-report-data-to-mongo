from collections import defaultdict
from collections import defaultdict
from helper import add_table,excel_update
import requests
from datetime import datetime
import json
from helper import add_table,excel_update
import paramiko

# get_total_space="sort(sum(uptycs_hdfs_node_config_capacity{cluster_id=~\"$cluster_id\", hdfsdatanode=~\"$data_node\"}) by (hdfsdatanode))"
get_total_space_query="sort(sum(uptycs_hdfs_node_config_capacity{cluster_id=~'clst1', hdfsdatanode=~'(s1c1dn1|s1c1dn2|s1c1dn3|s1c1dn4|s1c1dn6|s1c2dn1|s1c2dn2|s1c2dn4|s1c2dn6)'}) by (hdfsdatanode))"
# remaining_space="sort(uptycs_hdfs_node_remaining_capacity{cluster_id=~\"$cluster_id\", hdfsdatanode=~\"$data_node\"})"
remaining_space_query="sort(uptycs_hdfs_node_remaining_capacity{cluster_id=~'clst1', hdfsdatanode=~'(s1c1dn1|s1c1dn2|s1c1dn3|s1c1dn4|s1c1dn6|s1c2dn1|s1c2dn2|s1c2dn4|s1c2dn6)'})"
kafka_disk_used_percentage="uptycs_percentage_used{partition=~'/data/kafka'}"

class DISK:
    def __init__(self,sprint,build,load_type,doc,curr_ist_start_time,curr_ist_end_time,save_current_build_data_path,report_docx_path,previous_excel_file_path,current_excel_file_path,prom_con_obj):
        self.doc = doc
        self.curr_ist_start_time=curr_ist_start_time
        self.curr_ist_end_time=curr_ist_end_time
        self.save_current_build_data_path=save_current_build_data_path
        self.nodes_file_path=prom_con_obj.nodes_file_path
        self.sprint=sprint
        self.build = build
        self.load_type = load_type
        self.prev_build = '-'
        self.report_docx_path=report_docx_path

        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_point_api_path



        self.previous_excel_file_path=previous_excel_file_path
        self.current_excel_file_path=current_excel_file_path

        with open(self.nodes_file_path, 'r') as file:
            self.nodes_data = json.load(file)

    def extract_data(self,query,time , TAG):
        final=dict()
        ist_time_format = '%Y-%m-%d %H:%M'
        start_time_utc = (datetime.strptime(time, ist_time_format))
        timestamp = int(start_time_utc.timestamp())
        final={}
        PARAMS = {
            'query': query,
            'time' : timestamp
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
        result = response.json()['data']['result']

        for res in result:
            datanode = res['metric'][TAG]
            remaining =  float(res['value'][1])
            final[datanode] = remaining
        return final 
    
    def calculate_disk_usage(self,TYPE):

        if TYPE == 'HDFS':
            total_space = self.extract_data(get_total_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_before_load = self.extract_data(remaining_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_after_load = self.extract_data(remaining_space_query,self.curr_ist_end_time,'hdfsdatanode')
            nodes = [node for node in remaining_space_before_load]
        elif TYPE=="KAFKA":
            total_space = defaultdict(lambda : 3.6*1e+12)
            used_space_before_load = self.extract_data(kafka_disk_used_percentage,self.curr_ist_start_time,'host_name')
            used_space_after_load = self.extract_data(kafka_disk_used_percentage,self.curr_ist_end_time,'host_name')
            nodes = [node for node in used_space_before_load]

        data_dict={}
        data_dict['title'] = f"{TYPE} disk space usage"
        data_dict['header'] =["Node" ,f"{TYPE} total space configured(TB)", f"{TYPE} disk used % before load" , f"{TYPE} disk used % after load" , f"{TYPE} used space during load (GB)"]
        data_dict['body']=[] 
        excel_dict={"body":[]}
        save_dict={}
        bytes_in_a_tb=1e+12

        for node in nodes:
            curr_list=[]
            excel_list=[]

            total = total_space[node]/bytes_in_a_tb
            if TYPE=='HDFS':
                remaining_before_load = remaining_space_before_load[node]/bytes_in_a_tb
                remaining_after_load = remaining_space_after_load[node]/bytes_in_a_tb
                percentage_used_before_load=((total-remaining_before_load)/total)*100
                percentage_used_after_load=((total-remaining_after_load)/total)*100
            elif TYPE=='KAFKA':
                percentage_used_before_load=used_space_before_load[node]
                percentage_used_after_load=used_space_after_load[node]

            used_space=(percentage_used_after_load-percentage_used_before_load)*total*(1024/100)

            curr_list.append((node,'-'))
            curr_list.append((round(total,2),'-'))
            curr_list.append((round(percentage_used_before_load,2),'-'))
            curr_list.append((round(percentage_used_after_load,2),'-'))
            curr_list.append((round((used_space),2) ,'-'))

            excel_list.append((node,node))
            excel_list.append(('-','-'))
            excel_list.append(('-',round((used_space),2)))

            save_dict[node] = used_space

            data_dict['body'].append(curr_list)
            excel_dict['body'].append(excel_list)
        return TYPE,data_dict,excel_dict,save_dict

   
    def pg_disk_calc(self):
        
        port = 22  # SSH port (default is 22)
        username = 'abacus'  # Replace with your SSH username
        password = 'abacus'  # Replace with your SSH password

        table_dict={}
        table_dict['title'] = f"PG disk space usage"
        table_dict['header'] =["partition" ,'master configdb node', 'standby configdb node']
        table_dict['body']=[] 
        excel_dict={"body":[]}
        save_dict={}
        commands = {'/pg' : "sudo du -sh /pg"  , '/data':"sudo du -sh /data"}

        for partition,command in commands.items():
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            save_dict[partition]={}
            curr_list=[]
            curr_list.append((partition,'-'))
            for config_node in self.nodes_data['pgnodes']:
                hostname = self.nodes_data[config_node]['lan_ip']
                
                try:
                    ssh_client.connect(hostname, port, username, password)
                    stdin, stdout, stderr = ssh_client.exec_command(command)
                    output = stdout.read().decode('utf-8')
                    output = output.split()[0]
                    errors = stderr.read().decode('utf-8')
                    if errors:
                        print("Errors:")
                        print(errors)
                except:
                    output=0
                finally:
                    ssh_client.close()
                save_dict[partition][config_node]=output
                curr_list.append((output,'-'))
            table_dict['body'].append(curr_list)

        return 'PG', table_dict,None,save_dict

    def save(self,_ ):
        TYPE , data_dict,excel_dict,save_dict=_
        self.doc = add_table(self.doc,data_dict=data_dict)
        
        if excel_dict:
            excel_update({f"{TYPE} disk used space":excel_dict} ,self.previous_excel_file_path , self.current_excel_file_path,self.build)

        with open(self.save_current_build_data_path, 'r') as file:
            current_build_data = json.load(file)
        with open(self.save_current_build_data_path, 'w') as file:
            current_build_data[f"{TYPE}_disk_used_space"] = save_dict
            json.dump(current_build_data, file, indent=4)


    def make_calculations(self):
        self.doc.add_heading("Disk Usages", level=2)
        self.save(self.calculate_disk_usage('KAFKA'))
        self.save(self.calculate_disk_usage('HDFS'))
        self.save(self.pg_disk_calc())
        return self.doc
    