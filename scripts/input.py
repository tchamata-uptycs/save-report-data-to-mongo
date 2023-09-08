import configparser
from settings import configuration

load_name_values = ['ControlPlane', 'SingleCustomer', 'MultiCustomer', 'CombinedLoad' , 'AWS_MultiCustomer','GCP_MultiCustomer']
load_type_values = ['Osquery', 'CloudQuery', 'KubeQuery']

def save_data(details,config,previous_input_path):
    prom_con_obj = configuration(test_env_file_name=details['test_env_file_name'] , fetch_node_parameters_before_generating_report=details['fetch_node_parameters_before_generating_report'])
    config["DEFAULT"] = details
    with open(previous_input_path, "w") as configfile:
        config.write(configfile)
    return prom_con_obj

def update_details(details,config=None,take_input=False):
    for key,val in details.items():
        Type =type(val)            
        if take_input == True:
            helper_text=''
            if key == "load_name":
                helper_text = f"(load name values must be one of the following : {str(load_name_values)})"
            elif key == "load_type":
                helper_text = f"(load type values must be one of the following : {str(load_type_values)})" 
            default = input(f"Enter {' '.join(str(key).split('_')).title()} {helper_text} : ").strip()
        else:
            default = config["DEFAULT"].get(key, val)
        if Type==bool:
            if default=="True":
                default=True
            else:
                default=False
        details[key] = Type(default)
    return details

def create_input_form():
    previous_input_path = f"{configuration().base_stack_config_path}/prev_inp.ini"
    config = configparser.ConfigParser()
    config.read(previous_input_path)
    details = {
            "test_env_file_name":'s1_nodes.json',
            "load_name": "SingleCustomer",
            "load_type":"Osquery",
            "start_time_str":  "2023-08-12 23:08",
            "load_duration_in_hrs": 10,
            "sprint": 138,
            "build": 138000,
            "start_margin_for_charts":  10,
            "end_margin_for_charts": 10,
            "add_disk_space_usage": True,
            "add_screenshots": True,
            "add_kafka_topics": True,
            "make_cpu_mem_comparisions": True,
            "fetch_node_parameters_before_generating_report" :  False
            }
    details=update_details(details,config=config,take_input=False)
    
    for key,val in details.items():
        print(f"{key} : {val}")

    user_input = input("Do you want to continue with the above details? (yes/no/exit) : ").strip().lower()

    if user_input in ['yes' , 'no']:
        if user_input == "yes":
            print("Continuing ...")
        elif user_input == "no":
            print("Please enter the load details ...(use the above details as reference)")
            details=update_details(details,take_input=True)
        prom_con_obj = save_data(details,config,previous_input_path)
        return details,prom_con_obj
    elif user_input=='exit':
        return None,None
    else:
        print("Invalid input! ")
        return create_input_form()

if __name__ == "__main__":
    details = create_input_form()
    print(details) 