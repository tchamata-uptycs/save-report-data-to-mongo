import os
from pathlib import Path
import time
from datetime import datetime
from screenshots import take_screenshots
from docx import Document
from memory_and_cpu_comparison import MC_comparisions
from add_kafka_topics import kafka_topics
import shutil
from datetime import datetime, timedelta
import json
from disk_space import DISK
from helper import add_screenshots_to_docx,add_load_details
from input import create_input_form

#remaining tasks : trino queries(to do) , stack details(simple manually), load specific details(simple manually), accuracies(done), observations(manual)

if __name__ == "__main__":
    s_at = time.perf_counter()
    variables , prom_con_obj =create_input_form()
    print("Details :")
    print(prom_con_obj)
    for key,val in variables.items():
        print(f"{key} : {val}")

    nodes_file_path = prom_con_obj.nodes_file_path
    print("nodes file path : " + nodes_file_path)

    panel_loading_time_threshold_sec=45
    thread_len=10
    #-------------------------------------------------------------------------------------------------

    start_time = datetime.strptime(variables["start_time_str"], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(hours=variables["load_duration_in_hrs"]) # Add the load time in hours
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M")# Convert the result back to a string

    with open(nodes_file_path , 'r') as file:
        stack_details = json.load(file)

    details_for_report =  {
                "stack":stack_details["stack"],
                'stack_url':stack_details["stack_url"],
                "sprint": f"{variables['sprint']}",
                "build": f"{variables['build']}",
                "load_type":f"{variables['load_type']}",
                "load_duration_in_hrs":f"{variables['load_duration_in_hrs']} hrs",
                "load_start_time_ist" : f"{variables['start_time_str']}",
                "load_end_time_ist" : f"{end_time_str}"
                }
    
    current_build_data = {
        "details":details_for_report
    }

    #-------------------------------------------------------------------------------------------------

    ROOT_PATH = prom_con_obj.ROOT_PATH

    SCREENSHOT_DIR= ROOT_PATH+"/grafana_screenshots"
    CURRENT_BASE = f'{ROOT_PATH}/generated_reports/{variables["sprint"]}/{variables["load_type"]}'
    PREVIOUS_BASE = f'{ROOT_PATH}/generated_reports/{variables["prev_sprint"]}/{variables["load_type"]}' 
    
    report_docx_path = Path(f'{CURRENT_BASE}/{variables["build"]}_{variables["start_time_str"]}_{variables["load_type"]}_complete_report.docx')
    overall_comparisions_docx_path = Path(f'{CURRENT_BASE}/{variables["build"]}_{variables["start_time_str"]}_{variables["load_type"]}_overall_container_comparisions.docx')
    
    save_current_build_data_path = Path(f'{CURRENT_BASE}/mem_cpu_comparision_data.json')
    fetch_prev_build_data_path = Path(f'{PREVIOUS_BASE}/mem_cpu_comparision_data.json')

    previous_excel_file_path = f'{PREVIOUS_BASE}/previous_trend_excel.xlsx'
    current_excel_file_path = f'{CURRENT_BASE}/previous_trend_excel.xlsx'

    do_not_modify=False
    if os.path.exists(CURRENT_BASE):
        print("base path exists")
        if os.path.exists(save_current_build_data_path):
            print("current build data exists")
            with open(save_current_build_data_path,'r') as file:
                curr_data = json.load(file)
            uuid = curr_data["details"]["load_start_time_ist"]
            prev_end_time = curr_data["details"]["load_end_time_ist"]
            prev_build = curr_data["details"]["build"]
            if variables["start_time_str"]!=uuid or end_time_str!=prev_end_time or curr_data['details']['stack']!=stack_details["stack"]:
                print(f"old previous excel path : {previous_excel_file_path}")
                if os.path.exists(current_excel_file_path):
                    previous_excel_file_path=f'{CURRENT_BASE}/old({prev_build})({uuid} to {prev_end_time})/previous_trend_excel.xlsx'
                print("excel file path changed to current sprint")
                print(f"new previous excel path : {previous_excel_file_path}")
                for filename in os.listdir(CURRENT_BASE):
                    old_file = os.path.join(CURRENT_BASE, filename)
                    destination_dirname = os.path.join(CURRENT_BASE,f"old({prev_build})({uuid} to {prev_end_time})")
                    destination_file_path = os.path.join(destination_dirname,filename)
                    os.makedirs(destination_dirname, exist_ok=True)
                    try:
                        shutil.move(old_file, destination_file_path)
                    except Exception as e:
                        print("Error: Unable to copy the file. ", type(e).__name__, "-", str(e))
                print("current files moved successfully")
            else:
                do_not_modify=True
    else:
        print("New directories created")
        os.makedirs(CURRENT_BASE, exist_ok=True)
    #-------------------------------------------------------------------------------
    if not do_not_modify:
        with open(save_current_build_data_path, 'w') as file:
            json.dump(current_build_data, file, indent=4)  # indent for pretty formatting
        print("Created new json file : ",save_current_build_data_path)
        
        
        doc = Document()
        doc.add_heading('Load Test Report', level=0)
        #------------------------load details--------------------------

        doc = add_load_details(doc,details_for_report)

        #-------------------------disk space--------------------------

        if variables["add_disk_space_usage"] and variables["load_type"] != "ControlPlane":
            print("Performing disk space calculations ...")
            calc = DISK(doc=doc,sprint=variables["sprint"],load_type=variables["load_type"],build=variables["build"],curr_ist_start_time=variables["start_time_str"],
                                curr_ist_end_time=end_time_str,
                                save_current_build_data_path=save_current_build_data_path,
                                report_docx_path=report_docx_path,
                                previous_excel_file_path=previous_excel_file_path,
                                current_excel_file_path=current_excel_file_path,
                                prom_con_obj=prom_con_obj)
            
            doc = calc.make_calculations()
    
        #------------------ add kafka topics ---------------------------------------

        if variables["add_kafka_topics"]:
            kafka_obj = kafka_topics(save_path=save_current_build_data_path,doc=doc,build=variables["build"],
                                    prev_path=fetch_prev_build_data_path,
                                    previous_excel_file_path=previous_excel_file_path,
                                    current_excel_file_path=current_excel_file_path,
                                    prom_con_obj=prom_con_obj,
                                    root_path=ROOT_PATH)
            doc=kafka_obj.add_topics_to_report()


        #------------------take screenshots and add to report---------------------------------------
        if variables["add_screenshots"]:
            dash_board_path= f'/d/{stack_details["dashboard_uid"]}/{stack_details["dashboard_name"]}'

            ss_object = take_screenshots(doc=doc,start_time_str=variables["start_time_str"],end_time_str=end_time_str,
                                SCREENSHOT_DIR=SCREENSHOT_DIR,table_ids=stack_details["grafana_table_ids"],start_margin=variables["start_margin"],end_margin=variables["end_margin"],
                                panel_loading_time_threshold_sec=panel_loading_time_threshold_sec,
                                thread_len=thread_len,
                                elk_url = stack_details["elk_url"],
                                prom_con_obj=prom_con_obj,
                                dash_board_path=dash_board_path
                                )
            grafana_ids=ss_object.capture_screenshots_add_get_ids()
            doc = add_screenshots_to_docx(doc,SCREENSHOT_DIR, grafana_ids,stack_details["grafana_table_ids"])
            f_at = time.perf_counter()
            print(f"Adding the Screenshots took : {round(f_at - s_at,2)} seconds in total")		

        #--------------------------------cpu and mem node-wise---------------------------------------
        if variables["make_cpu_mem_comparisions"]:

            print("Performing node-wise comparisions ...")
            comp = MC_comparisions(doc=doc,sprint=variables["sprint"],load_type=variables["load_type"],build=variables["build"],curr_ist_start_time=variables["start_time_str"],
                                curr_ist_end_time=end_time_str,
                                save_current_build_data_path=save_current_build_data_path,
                                fetch_prev_build_data_path=fetch_prev_build_data_path,
                                overall_comparisions_docx_path=overall_comparisions_docx_path,
                                previous_excel_file_path=previous_excel_file_path,
                                current_excel_file_path=current_excel_file_path,
                                show_gb_cores=variables["show_gb_cores"],
                                prom_con_obj=prom_con_obj)
            doc = comp.make_comparisions()

        #-----------------------save main report--------------------------
        doc.save(report_docx_path)
        print("Saved the report")
        #-------------------------------------------------------------
        f3_at = time.perf_counter()
        print(f"Preparing the report took : {round(f3_at - s_at,2)} seconds in total")
    else:
        print(f"Files not modified as a report for this load time for stack {stack_details['stack']} is already generated previously")
    