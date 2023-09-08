import paramiko
import json

class kafka_topics:
    def __init__(self,save_path,root_path,prom_con_obj):
        self.save_path = save_path
        self.local_script_path = f'{root_path}/kafka_topics.py'
        self.host = prom_con_obj.execute_kafka_topics_script_in
        self.port=prom_con_obj.ssh_port
        self.username = prom_con_obj.abacus_username
        self.password  = prom_con_obj.abacus_password
        self.remote_directory = f'/home/{self.username}'

    def add_topics_to_report(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"Executing kafka topics script in host {self.host}")
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

            with open(self.save_path, 'r') as file:
                current_build_data = json.load(file)
            current_build_data["kafka_topics"] = output_list
            print("Saving kafka topics ...")
            with open(self.save_path, 'w') as file:
                json.dump(current_build_data, file, indent=4)  

        finally:
            ssh.close()