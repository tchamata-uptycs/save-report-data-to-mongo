import requests
import json
import paramiko

class DISK:
    def __init__(self,start_timestamp,end_timestamp,prom_con_obj):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.test_env_file_path=prom_con_obj.test_env_file_path
        self.PROMETHEUS = prom_con_obj.prometheus_path
        self.API_PATH = prom_con_obj.prom_point_api_path
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        with open(self.test_env_file_path, 'r') as file:
            self.stack_details = json.load(file)

        dnode_pattern=''
        for dnode in self.stack_details['dnodes']:
            dnode_pattern+=dnode+'|'
        dnode_pattern=dnode_pattern[:-1]
        self.kafka_total_space = {}
        for pnode in self.stack_details['pnodes']:
            capacity = self.stack_details[pnode]['storage']['kafka']
            if str(capacity).endswith('T'):
                self.kafka_total_space[pnode] = float(str(capacity)[:-1]) * 1e+12
                self.kafka_total_space[pnode+'v'] = float(str(capacity)[:-1]) * 1e+12
            elif str(capacity).endswith('G'):
                self.kafka_total_space[pnode] = float(str(capacity)[:-1]) * 1e+9
                self.kafka_total_space[pnode+'v'] = float(str(capacity)[:-1]) * 1e+9

        self.get_total_space_query=f"sort(sum(uptycs_hdfs_node_config_capacity{{cluster_id=~'clst1', hdfsdatanode=~'({dnode_pattern})'}}) by (hdfsdatanode))"
        self.remaining_hdfs_space_query=f"sort(uptycs_hdfs_node_remaining_capacity{{cluster_id=~'clst1', hdfsdatanode=~'({dnode_pattern})'}})"
        self.kafka_disk_used_percentage="uptycs_percentage_used{partition=~'/data/kafka'}"

    def extract_data(self,query,timestamp , TAG):
        final=dict()
        final={}
        PARAMS = {
            'query': query,
            'time' : timestamp
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
        result = response.json()['data']['result']

        for res in result:
            node = res['metric'][TAG]
            remaining =  float(res['value'][1])
            final[node] = remaining
        return final 
    
    def calculate_disk_usage(self,TYPE):
        if TYPE == 'hdfs':
            total_space = self.extract_data(self.get_total_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_before_load = self.extract_data(self.remaining_hdfs_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_after_load = self.extract_data(self.remaining_hdfs_space_query,self.curr_ist_end_time,'hdfsdatanode')
            nodes = [node for node in remaining_space_before_load]
        elif TYPE=="kafka":
            total_space=self.kafka_total_space
            used_space_before_load = self.extract_data(self.kafka_disk_used_percentage,self.curr_ist_start_time,'host_name')
            used_space_after_load = self.extract_data(self.kafka_disk_used_percentage,self.curr_ist_end_time,'host_name')
            nodes = [node for node in used_space_before_load]

        save_dict={}
        bytes_in_a_tb=1e+12

        for node in nodes:
            total = total_space[node]/bytes_in_a_tb
            if TYPE=='hdfs':
                remaining_before_load = remaining_space_before_load[node]/bytes_in_a_tb
                remaining_after_load = remaining_space_after_load[node]/bytes_in_a_tb
                percentage_used_before_load=((total-remaining_before_load)/total)*100
                percentage_used_after_load=((total-remaining_after_load)/total)*100
            elif TYPE=='kafka':
                percentage_used_before_load=used_space_before_load[node]
                percentage_used_after_load=used_space_after_load[node]
            used_space=(percentage_used_after_load-percentage_used_before_load)*total*(1024/100)
            save_dict[node] = {f"{TYPE}_total_space_configured_in_tb" : total , f"{TYPE}_disk_used_percentage_before_load" :percentage_used_before_load,f"{TYPE}_disk_used_percentage_after_load":percentage_used_after_load,f"{TYPE} used_space_during_load_in_gb":used_space}

        return TYPE,save_dict

    def pg_disk_calc(self):
        save_dict={}
        commands = {'/pg' : "sudo du -sh /pg"  , '/data':"sudo du -sh /data"}
        for partition,command in commands.items():
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            save_dict[partition]={}
            for config_node in self.stack_details['pgnodes']:                
                try:
                    ssh_client.connect(config_node, self.port, self.username, self.password)
                    stdin, stdout, stderr = ssh_client.exec_command(command)
                    output = stdout.read().decode('utf-8')
                    output = output.split()[0]
                    errors = stderr.read().decode('utf-8')
                    if errors:
                        print("Errors:")
                        print(errors)
                except Exception as e:
                    print("ERROR : ",str(e))
                    output=0
                finally:
                    ssh_client.close()
                save_dict[partition][config_node]=output
        return 'pg',save_dict

    def save(self,_ ,current_build_data):
        TYPE ,save_dict=_
        current_build_data[f"{TYPE}_disk_used_space"] = save_dict
        return current_build_data
    
    def make_calculations(self):
        current_build_data={}
        current_build_data=self.save(self.calculate_disk_usage('kafka'),current_build_data)
        current_build_data=self.save(self.calculate_disk_usage('hdfs'),current_build_data)
        return current_build_data
    