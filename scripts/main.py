import sys
from pathlib import Path
import time
from datetime import datetime
from screenshots import take_screenshots
from memory_and_cpu_comparison import MC_comparisions
from add_kafka_topics import kafka_topics
from datetime import datetime, timedelta
import json
from disk_space import DISK
from helper import add_screenshots_to_docx,push_data_to_mongo
from input import create_input_form

if __name__ == "__main__":
    s_at = time.perf_counter()
    variables , prom_con_obj =create_input_form()
    if not variables or not prom_con_obj : 
        print("Received NoneType objects, terminating the program ...")
        sys.exit()
    print("Details :")
    for key,val in variables.items():
        print(f"{key} : {val}")

    test_env_file_path = prom_con_obj.test_env_file_path
    print("test environment file path : " + test_env_file_path)

    panel_loading_time_threshold_sec=45
    thread_len=10
    #-------------------------------------------------------------------------------------------------

    start_time = datetime.strptime(variables["start_time_str"], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(hours=variables["load_duration_in_hrs"]) # Add the load time in hours
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M")# Convert the result back to a string

    with open(test_env_file_path , 'r') as file:
        test_env_json_details = json.load(file)

    details_for_report =  {
                "stack":test_env_json_details["stack"],
                "sprint": f"{variables['sprint']}",
                "build": f"{variables['build']}",
                "load_name":f"{variables['load_name']}",
                "load_duration_in_hrs":f"{variables['load_duration_in_hrs']} hrs",
                "load_start_time_ist" : f"{variables['start_time_str']}",
                "load_end_time_ist" : f"{end_time_str}"
                }
    
    #------------------------- Load specific details -------------------
    with open(f"{prom_con_obj.base_stack_config_path}/load_specific_details.json" , 'r') as file:
        load_specific_details = json.load(file)
    details_for_report.update(load_specific_details[details_for_report["load_name"]])
    #------------------------load and test env details--------------------------
    current_build_data = {"details":details_for_report , "test_environment_details":test_env_json_details}
    ROOT_PATH = prom_con_obj.ROOT_PATH
    SCREENSHOT_DIR= f"{ROOT_PATH}/grafana_screenshots"
    save_current_build_data_path = Path(f'{ROOT_PATH}/mem_cpu_comparision_data.json')

    with open(save_current_build_data_path, 'w') as file:
        json.dump(current_build_data, file, indent=4)  # indent for pretty formatting

    print("Created new json file : ",save_current_build_data_path)

    #-------------------------disk space--------------------------

    if variables["add_disk_space_usage"] and variables["load_name"] != "ControlPlane":
        print("Performing disk space calculations ...")
        calc = DISK(sprint=variables["sprint"],build=variables["build"],curr_ist_start_time=variables["start_time_str"],
                            curr_ist_end_time=end_time_str,
                            save_current_build_data_path=save_current_build_data_path,
                            prom_con_obj=prom_con_obj)
        
        calc.make_calculations()

    #------------------ add kafka topics ---------------------------------------

    if variables["add_kafka_topics"]:
        kafka_obj = kafka_topics(save_path=save_current_build_data_path,build=variables["build"],
                                prom_con_obj=prom_con_obj,
                                root_path=ROOT_PATH)
        kafka_obj.add_topics_to_report()

    #------------------take screenshots and add to report---------------------------------------
    if variables["add_screenshots"]:
        dash_board_path= f'/d/{test_env_json_details["dashboard_uid"]}/{test_env_json_details["dashboard_name"]}'

        ss_object = take_screenshots(start_time_str=variables["start_time_str"],end_time_str=end_time_str,
                            SCREENSHOT_DIR=SCREENSHOT_DIR,table_ids=test_env_json_details["grafana_table_ids"],start_margin=variables["start_margin_for_charts"],end_margin=variables["end_margin_for_charts"],
                            panel_loading_time_threshold_sec=panel_loading_time_threshold_sec,
                            thread_len=thread_len,
                            elk_url = test_env_json_details["elk_url"],
                            prom_con_obj=prom_con_obj,
                            dash_board_path=dash_board_path
                            )
        grafana_ids=ss_object.capture_screenshots_add_get_ids()
        add_screenshots_to_docx(SCREENSHOT_DIR, grafana_ids,test_env_json_details["grafana_table_ids"])
        f_at = time.perf_counter()
        print(f"Collecting the Screenshots took : {round(f_at - s_at,2)} seconds in total")     

    #--------------------------------cpu and mem node-wise---------------------------------------
    if variables["make_cpu_mem_comparisions"]:

        print("Performing node-wise comparisions ...")
        comp = MC_comparisions(sprint=variables["sprint"],build=variables["build"],curr_ist_start_time=variables["start_time_str"],
                            curr_ist_end_time=end_time_str,
                            save_current_build_data_path=save_current_build_data_path,
                            show_gb_cores=False,
                            prom_con_obj=prom_con_obj)
        comp.make_comparisions()

   
    #----------------Saving the json data to mongo--------------------
    push_data_to_mongo(variables['load_name'],variables['load_type'],save_current_build_data_path,prom_con_obj)
    #-----------------------------------------------------------------
    f3_at = time.perf_counter()
    print(f"Preparing the report took : {round(f3_at - s_at,2)} seconds in total")

