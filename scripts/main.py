import sys,os
from pathlib import Path
import time
import pymongo
from datetime import datetime, timedelta
import json
from datetime import datetime
from screenshots import take_screenshots
from memory_and_cpu_usages import MC_comparisions
from osquery.add_kafka_topics import kafka_topics
from disk_space import DISK
from helper import push_data_to_mongo
from input import create_input_form

if __name__ == "__main__":
    s_at = time.perf_counter()
    variables , prom_con_obj =create_input_form()
    if not variables or not prom_con_obj : 
        print("Received NoneType objects, terminating the program ...")
        sys.exit()
    TEST_ENV_FILE_PATH   = prom_con_obj.test_env_file_path
    print("test environment file path : " + TEST_ENV_FILE_PATH)
    #-------------------------------------------------------------------------------------------------
    start_time = datetime.strptime(variables["start_time_str_ist"], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(hours=variables["load_duration_in_hrs"])
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M")

    with open(TEST_ENV_FILE_PATH , 'r') as file:
        test_env_json_details = json.load(file)
    skip_fetching_data=False
    #---------------------Check for previous runs------------------------------------
    mongo_connection_string=prom_con_obj.mongo_connection_string
    client = pymongo.MongoClient(mongo_connection_string)
    db=client[variables['load_type']+"_LoadTests"]
    collection = db[variables["load_name"]]

    if variables['save_report_data_to_database'] == True:
        documents_with_same_load_time_and_stack = collection.find({"details.sprint":variables['sprint'] ,"details.stack":test_env_json_details["stack"] , "details.load_start_time_ist":f"{variables['start_time_str_ist']}" , "details.load_duration_in_hrs":variables['load_duration_in_hrs']})
        if len(list(documents_with_same_load_time_and_stack)) > 0:
            print(f"ERROR! A document with load time ({variables['start_time_str_ist']}) - ({end_time_str}) on {test_env_json_details['stack']} for this sprint for {variables['load_type']}-{variables['load_name']} load is already available.")
            skip_fetching_data=True
    if skip_fetching_data == False:
        run=1
        documents_with_same_sprint = list(collection.find({"details.sprint":139} , {"details.run":1}))
        if len(documents_with_same_sprint)>0:
            max_run = 0
            for document in documents_with_same_sprint :
                max_run = max(document['details']['run'] , max_run)
            run=max_run+1
            print(f"you have already saved the details for this load in this sprint, setting run value to {run}")
        #------------------------------------------------------------------------
        details_for_report =  {
            "stack":test_env_json_details["stack"],
            "sprint": variables['sprint'],
            "build": variables['build'],
            "load_name":f"{variables['load_name']}",
            "load_type":f"{variables['load_type']}",
            "load_duration_in_hrs":variables['load_duration_in_hrs'],
            "load_start_time_ist" : f"{variables['start_time_str_ist']}",
            "load_end_time_ist" : f"{end_time_str}",
            "run":run,
            }
        #------------------------- Load specific details -------------------

        with open(f"{prom_con_obj.base_stack_config_path}/load_specific_details.json" , 'r') as file:
            load_specific_details = json.load(file)

        #------------------------load and test env details--------------------------
        
        current_build_data = {"details":details_for_report , "load_specific_details":load_specific_details[variables['load_name']] ,"test_environment_details":test_env_json_details}
        ROOT_PATH = prom_con_obj.ROOT_PATH
        SCREENSHOT_DIR= f"{ROOT_PATH}/grafana_screenshots"
        save_current_build_data_path = Path(f'{prom_con_obj.base_stack_config_path}/current_report_data.json')
        with open(save_current_build_data_path, 'w') as file:
            json.dump(current_build_data, file, indent=4) 

        #-------------------------disk space--------------------------

        if variables["add_disk_space_usage"] == True and variables["load_name"] != "ControlPlane":
            print("Performing disk space calculations ...")
            calc = DISK(curr_ist_start_time=variables["start_time_str_ist"],curr_ist_end_time=end_time_str,
                        save_current_build_data_path=save_current_build_data_path,prom_con_obj=prom_con_obj)
            
            calc.make_calculations()

        #--------------------------------- add kafka topics ---------------------------------------

        if variables["add_kafka_topics"]==True:
            print("Add kafka topics ...")
            kafka_obj = kafka_topics(save_path=save_current_build_data_path,prom_con_obj=prom_con_obj,root_path=ROOT_PATH)
            kafka_obj.add_topics_to_report()

        #---------------------------take screenshots and add to report------------------------------
        grafana_ids=None
        if variables["add_screenshots"]==True and variables['save_report_data_to_database'] == True:
            print("Collecting screenshots ...")
            dash_board_path= f'/d/{test_env_json_details["dashboard_uid"]}/{test_env_json_details["dashboard_name"]}'
            ss_object = take_screenshots(start_time_str_ist=variables["start_time_str_ist"],end_time_str=end_time_str,
                                SCREENSHOT_DIR=SCREENSHOT_DIR,table_ids=test_env_json_details["grafana_table_ids"],
                                start_margin=10,
                                end_margin=variables["add_extra_time_for_charts_at_end_in_min"],
                                elk_url = test_env_json_details["elk_url"],
                                prom_con_obj=prom_con_obj,
                                dash_board_path=dash_board_path
                                )
            grafana_ids=ss_object.capture_screenshots_add_get_ids()
            f_at = time.perf_counter()
            print(f"Collecting the Screenshots took : {round(f_at - s_at,2)} seconds in total")     

        #--------------------------------cpu and mem node-wise---------------------------------------

        if variables["make_cpu_mem_comparisions"]==True:
            print("Fetching resource usages ...")
            comp = MC_comparisions(curr_ist_start_time=variables["start_time_str_ist"],curr_ist_end_time=end_time_str,
                    save_current_build_data_path=save_current_build_data_path,show_gb_cores=False,prom_con_obj=prom_con_obj)
            comp.make_comparisions()

        #----------------Saving the json data to mongo--------------------
        if variables['save_report_data_to_database'] == True:
            print("Savig data to mongoDB ...")
            push_data_to_mongo(variables['load_name'],variables['load_type'],save_current_build_data_path,mongo_connection_string,SCREENSHOT_DIR, grafana_ids,test_env_json_details["grafana_table_ids"])
        #-----------------------------------------------------------------
        f3_at = time.perf_counter()
        print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
    

