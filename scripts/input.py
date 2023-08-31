import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import configparser
import json
from prometeus_utils import PrometheusConnector
import os

config_path = list(os.listdir(PrometheusConnector().base_stack_config_path))
previous_input_path = f"{PrometheusConnector().base_stack_config_path}/prev_inp.ini"
all_stack_config_paths = [filename for filename in config_path if filename.endswith('.json')]

config = configparser.ConfigParser()
config.read(previous_input_path)

load_type_values = ['ControlPlane', 'SingleCustomer', 'MultiCustomer', 'CombinedLoad']

prom_con_obj=None
details = {
        "nodes_file_name":[str , 's1_nodes.json'],
        "load_type": [str , "SingleCustomer"],
        "start_time_str": [str , "2023-08-12 23:08"],
        "load_time_in_hrs": [int , 10],
        "sprint": [str , 138],
        "build": [str , 138000],
        "prev_sprint": [str , 137],
        "start_margin": [int , 10],
        "end_margin": [int , 10],
        "show_gb_cores": [bool , False],
        "add_disk_space_usage":[bool , True],
        "add_screenshots":[bool , True],
        "add_kafka_topics":[bool , True],
        "make_cpu_mem_comparisions":[bool , True],
        }

def create_input_form():
    global prom_con_obj,details
    def center_window(root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")

    def cancel():
        global prom_con_obj,details
        for key in details:
            details[key]=None
        prom_con_obj = None
        root.quit()

    def save_data(details):
        global prom_con_obj
        prom_con_obj = PrometheusConnector(nodes_file_name=details['nodes_file_name'])
        config["DEFAULT"] = details
        with open(previous_input_path, "w") as configfile:
            config.write(configfile)
        return prom_con_obj
    def submit():
        global prom_con_obj,details
        for (key,val) in details.items():
            Type , default , var = val
            details[key] = Type(var.get())
        # prom_con_obj = PrometheusConnector(nodes_file_name=details['nodes_file_name'])
        # config["DEFAULT"] = details
        # with open(previous_input_path, "w") as configfile:
        #     config.write(configfile)
        prom_con_obj = save_data(details)
        stack = details['nodes_file_name'].split('_')[0]

        confirm = messagebox.askokcancel("Confirmation", f"Are you sure that the details mentioned are correct for generating a report for stack {stack} ?")

        if confirm:
            root.quit()
    try: 
        root = tk.Tk()
        root.title("Enter the load details for report generation")
        center_window(root, 520, 550)  # Center the window and set dimensions

        for id , (key,val) in enumerate(details.items()):
            Type , default = val
            label = ttk.Label(root, text=key)
            label.grid(row=id, column=0)

            if Type == bool:
                var = tk.BooleanVar()  #bool
                entry = ttk.Checkbutton(root, variable=var)
                
            else:
                var = tk.StringVar()  #string
                if key == "load_type":
                    entry = ttk.Combobox(root, textvariable=var, values=load_type_values, state="readonly")
                elif key == "nodes_file_name":
                    entry = ttk.Combobox(root, textvariable=var, values=all_stack_config_paths, state="readonly")
                else:
                    entry = ttk.Entry(root, textvariable=var)

            var.set(config["DEFAULT"].get(key, default))
            entry.grid(row=id, column=1)
            details[key].append(var)

        # Function to update Previous Sprint based on Sprint
        def update_prev_sprint(*args):
            sprint_value = details['sprint'][2].get()
            try:
                prev_sprint_value = int(sprint_value) - 1
            except ValueError:
                prev_sprint_value = ""
            details['prev_sprint'][2].set(str(prev_sprint_value))
        details['sprint'][2].trace("w", update_prev_sprint)

        #submit button
        submit_button = ttk.Button(root, text="Generate", command=submit)
        submit_button.grid(row=15, column=1)

        # Cancel Button
        cancel_button = ttk.Button(root, text="Cancel", command=cancel)
        cancel_button.grid(row=15, column=0)

        root.mainloop()
        root.quit()

        return details,prom_con_obj

    except Exception as e:
        print(str(e))
        print("Looks like tkinter canvas is having an issue, do you want to continue with these details?")

        for key,val in details.items():
            print(f"{key} : {val[1]}")
        
        user_input = input("Select yes to continue, select no to enter new details ... ").strip().lower()

        if user_input in ['yes' , 'no']:
            if user_input == "yes":
                print("Continuing ...")
                for key ,val in details.items():
                    details[key] = val[1]

            elif user_input == "no":
                print("Please enter your details manually to proceed...(use above details as reference)")
                for key,val in details.items():
                    details[key] = val[0](input(f"Enter {key} :").strip())

            # prom_con_obj = PrometheusConnector(nodes_file_name=details['nodes_file_name'])
            # config["DEFAULT"] = details
            # with open(previous_input_path, "w") as configfile:
            #     config.write(configfile)
            prom_con_obj = save_data(details)

            return details,prom_con_obj
        
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            return None


if __name__ == "__main__":
    details = create_input_form()
    print(details)  # Print the details to verify that they are read from the configuration