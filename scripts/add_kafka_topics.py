import paramiko
import json
import os
from helper import add_table,excel_update

class kafka_topics:
    # Create an SSH client
    def __init__(self,save_path , doc,build,prev_path,previous_excel_file_path,current_excel_file_path,root_path,prom_con_obj):
        self.save_path = save_path
        self.doc = doc
        self.build = build
        self.prev_path = prev_path
        self.previous_excel_file_path=previous_excel_file_path
        self.current_excel_file_path=current_excel_file_path
        self.local_script_path = f'{root_path}/kafka_topics.py'
        self.host = prom_con_obj.execute_kafka_topics_script_in
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.remote_directory = f'/home/{self.username}'

    def get_data_dict(self,curr_list,prev_list):
        data_dict=dict()
        data_dict["header"] = [self.build]
        data_dict["body"] = []
        data_dict["title"] = "Kafka topics"
        matched='Old Topics : '
        not_matched='New Topics : '
        new_topics_created=False
        for new in curr_list:
            if new in prev_list:
                matched+=' '+new
            else:
                not_matched+=' '+new
                new_topics_created=True
        
        text="Summary : "

        if new_topics_created:
            text += "New topics found"
            data_dict["body"].append([( text ,"red")])
        else:
            text += "No new topics added"
            data_dict["body"].append([( text,"green")])

        data_dict["body"].append([( not_matched ,"red")])
        data_dict["body"].append([( matched )])

        return data_dict
    
    def get_kafka_excel_dict(self,lst):
        data_dict=[]
        for topic in lst:
            data_dict.append([(topic) , (topic)])
        return data_dict
        
    def add_topics_to_report(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"Executing kafka topics script in {self.host}")
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            remote_script_path = f'{self.remote_directory}/kafka_new_topic.py'
            sftp.put(self.local_script_path, remote_script_path)
            print(f"The script '{remote_script_path}' has been uploaded to the remote server.")

            remote_command = f'python3 {remote_script_path}'
            stdin, stdout, stderr = ssh.exec_command(remote_command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()

            output_list = [line for line in output.split('\n') if line.strip()][:-1]

            if os.path.exists(self.prev_path):
                with open(self.prev_path , 'r') as file:
                    prev_data = json.load(file)
                    try:
                        prev_list = prev_data["kafka_topics"]
                    except:
                        prev_list = []
            else:
                prev_list=[]

            self.doc = add_table(self.doc,self.get_data_dict(output_list,prev_list))

            with open(self.save_path, 'r') as file:
                current_build_data = json.load(file)
            current_build_data["kafka_topics"] = output_list
            print("Saving kafka topics ...")
            with open(self.save_path, 'w') as file:
                json.dump(current_build_data, file, indent=4)  # indent for pretty formatting

            sheets={
                "kafka topics" : self.get_kafka_excel_dict(output_list),
            }

            excel_update(sheets , self.previous_excel_file_path, self.current_excel_file_path , self.build)

        finally:
            # Close the SSH connection
            ssh.close()
        return self.doc