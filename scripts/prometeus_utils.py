import json

class PrometheusConnector:
    def __init__(self,nodes_file_name=None, username='masabathulararao'):
        self.prometheus_port = "9090"
        self.prom_api_path = "/api/v1/query_range"
        self.prom_point_api_path = "/api/v1/query"
        self.ROOT_PATH = f"/Users/{username}/Documents/Loadtest"
        self.base_stack_config_path = f"{self.ROOT_PATH}/stack_config_files"

        if nodes_file_name:
            self.nodes_file_path = f"{self.base_stack_config_path}/{nodes_file_name}"
            with open(self.nodes_file_path , 'r') as file:
                stack_details = json.load(file)
                
            self.monitoring_ip=  stack_details[stack_details["monitoring_node"]]["lan_ip"]
            self.prometheus_path = f"http://{self.monitoring_ip}:{self.prometheus_port}"

        self.GRAFANA_USERNAME="admin"
        self.GRAFANA_PASSWORD="admin123"
        self.GRAFANA_PORT = "3000"
        self.username=username