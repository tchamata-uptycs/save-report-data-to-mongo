import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import configparser
import json
from prometeus_utils import PrometheusConnector
import os

all_stack_config_paths = list(os.listdir(PrometheusConnector().base_stack_config_path))

config = configparser.ConfigParser()
config.read("config.ini")

details = {
        "load_type": None,
        "start_time_str": None,
        "load_time_in_hrs": None,
        "sprint": None,
        "build": None,
        "prev_sprint": None,
        "start_margin": None,
        "end_margin": None,
        "prom_con_obj":None,
        "show_gb_cores": None,
        "add_disk_space_usage":None,
        "add_screenshots":None,
        "add_kafka_topics":None,
        "make_cpu_mem_comparisions":None,
        }

def create_input_form():
    def center_window(root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")

    def cancel():
        for key in details:
            details[key]=None
        root.quit()

    def submit():
            
        details["load_type"] = load_type_var.get()
        details["start_time_str"] = start_time_var.get()
        details["load_time_in_hrs"] = int(load_time_entry.get())
        details["sprint"] = sprint_entry.get()
        details["build"] = build_entry.get()
        details["prev_sprint"] = prev_sprint_var.get()
        details["start_margin"] = int(start_margin_entry.get())
        details["end_margin"] = int(end_margin_entry.get())
        details["show_gb_cores"] = show_gb_cores_var.get()

        details["add_disk_space_usage"] = add_disk_space_usage_var.get()
        details["add_kafka_topics"] = add_kafka_topics_var.get()
        details["add_screenshots"] = add_screenshots_var.get()
        details["make_cpu_mem_comparisions"] = make_cpu_mem_comparisions_var.get()

        nodes_file_name=config_path_var.get()

        prom_con_obj = PrometheusConnector(nodes_file_name=nodes_file_name)

        with open(prom_con_obj.nodes_file_path , 'r') as file:
            stack_details = json.load(file)
        stack=stack_details["stack"]

        details["prom_con_obj"] = prom_con_obj

        # Update the configuration with the new values
        config["DEFAULT"] = details

        # Save the updated configuration to the file
        with open("config.ini", "w") as configfile:
            config.write(configfile)


        # Display a confirmation dialog
        confirm = messagebox.askokcancel("Confirmation", f"Are you sure that the details mentioned are correct for generating a report for stack {stack} ?")

        if confirm:
            root.quit()

    def select_date():
        date_str = simpledialog.askstring("Input", "Enter Start Date (YYYY-MM-DD HH:MM)")
        if date_str:
            start_time_var.set(date_str)

    try:
        1/0
        root = tk.Tk()
        root.title("Enter the load details for report generation")
        center_window(root, 520, 550)  # Center the window and set dimensions



        # stack file path
        config_path_label = ttk.Label(root, text="Stack config file path")
        config_path_label.grid(row=0, column=0)
        config_path_var = tk.StringVar()
        config_path_values = all_stack_config_paths
        config_path_combo = ttk.Combobox(root, textvariable=config_path_var, values=config_path_values, state="readonly")
        config_path_var.set('s1_nodes.json')
        config_path_combo.grid(row=0, column=1)


        # Load Type
        load_type_label = ttk.Label(root, text="Load Type")
        load_type_label.grid(row=1, column=0)
        load_type_var = tk.StringVar()
        load_type_values = ['ControlPlane', 'SingleCustomer', 'MultiCustomer', 'CombinedLoad']
        load_type_combo = ttk.Combobox(root, textvariable=load_type_var, values=load_type_values, state="readonly")

        # Set the default value from the configuration
        load_type_var.set(config["DEFAULT"].get("load_type", 'SingleCustomer'))

        load_type_combo.grid(row=1, column=1)


        # Start Time
        start_time_label = ttk.Label(root, text="Load Start Time")
        start_time_label.grid(row=2, column=0)
        start_time_var = tk.StringVar()
        start_time_entry = ttk.Entry(root, textvariable=start_time_var)
        
        # Set the default value from the configuration
        start_time_var.set(config["DEFAULT"].get("start_time_str", "2023-08-11 23:08"))
        
        start_time_entry.grid(row=2, column=1)

        # Date Picker Button
        date_picker_button = ttk.Button(root, text="Pick Date", command=select_date)
        date_picker_button.grid(row=2, column=2)

        # Load Time in Hours
        load_time_label = ttk.Label(root, text="Total Load Duration (hrs)")
        load_time_label.grid(row=3, column=0)
        load_time_entry = ttk.Entry(root)
        
        # Set the default value from the configuration
        load_time_entry.insert(0, config["DEFAULT"].get("load_time_in_hrs", "10"))
        
        load_time_entry.grid(row=3, column=1)

        # Sprint
        sprint_label = ttk.Label(root, text="Current Sprint")
        sprint_label.grid(row=4, column=0)
        sprint_var = tk.StringVar()
        sprint_entry = ttk.Entry(root, textvariable=sprint_var)
        
        # Set the default value from the configuration
        sprint_entry.insert(0, config["DEFAULT"].get("sprint", "137"))
        
        sprint_entry.grid(row=4, column=1)

        # Previous Sprint
        prev_sprint_label = ttk.Label(root, text="Previous Sprint")
        prev_sprint_label.grid(row=5, column=0)
        prev_sprint_var = tk.StringVar()
        prev_sprint_entry = ttk.Entry(root, textvariable=prev_sprint_var)
        
        # Set the default value from the configuration
        prev_sprint_entry.insert(0, config["DEFAULT"].get("prev_sprint", "136"))
        
        prev_sprint_entry.grid(row=5, column=1)

        # Function to update Previous Sprint based on Sprint
        def update_prev_sprint(*args):
            sprint_value = sprint_var.get()
            try:
                prev_sprint_value = int(sprint_value) - 1
            except ValueError:
                prev_sprint_value = ""
            prev_sprint_var.set(str(prev_sprint_value))
        
        # Attach the update function to the Sprint field
        sprint_var.trace("w", update_prev_sprint)

        # Build
        build_label = ttk.Label(root, text="Current Build")
        build_label.grid(row=6, column=0)
        build_entry = ttk.Entry(root)
        
        # Set the default value from the configuration
        build_entry.insert(0, config["DEFAULT"].get("build", "137006"))
        
        build_entry.grid(row=6, column=1)

        # Start Margin
        start_margin_label = ttk.Label(root, text="Charts start time margin")
        start_margin_label.grid(row=7, column=0)
        start_margin_entry = ttk.Entry(root)
        
        # Set the default value from the configuration
        start_margin_entry.insert(0, config["DEFAULT"].get("start_margin", "10"))
        
        start_margin_entry.grid(row=7, column=1)

        # End Margin
        end_margin_label = ttk.Label(root, text="Charts end time Margin")
        end_margin_label.grid(row=8, column=0)
        end_margin_entry = ttk.Entry(root)
        
        # Set the default value from the configuration
        end_margin_entry.insert(0, config["DEFAULT"].get("end_margin", "10"))
        
        end_margin_entry.grid(row=8, column=1)

        # Show GB Cores
        show_gb_cores_label = ttk.Label(root, text="Show GB/Cores for comparisions")
        show_gb_cores_label.grid(row=9, column=0)
        show_gb_cores_var = tk.BooleanVar()
        show_gb_cores_check = ttk.Checkbutton(root, variable=show_gb_cores_var)
        show_gb_cores_var.set(config["DEFAULT"].get("show_gb_cores", False))
        show_gb_cores_check.grid(row=9, column=1)

        add_disk_space_usage_label = ttk.Label(root, text="Add Disk space usages")
        add_disk_space_usage_label.grid(row=10, column=0)
        add_disk_space_usage_var = tk.BooleanVar()
        add_disk_space_usage_check = ttk.Checkbutton(root, variable=add_disk_space_usage_var)
        add_disk_space_usage_var.set(config["DEFAULT"].get("add_disk_space_usage", True))
        add_disk_space_usage_check.grid(row=10, column=1)

        add_kafka_topics_label = ttk.Label(root, text="Add Kafka Topics")
        add_kafka_topics_label.grid(row=11, column=0)
        add_kafka_topics_var = tk.BooleanVar()
        add_kafka_topics_check = ttk.Checkbutton(root, variable=add_kafka_topics_var)
        add_kafka_topics_var.set(config["DEFAULT"].get("add_kafka_topics", True))
        add_kafka_topics_check.grid(row=11, column=1)

        add_screenshots_label = ttk.Label(root, text="Add Grafana Charts")
        add_screenshots_label.grid(row=12, column=0)
        add_screenshots_var = tk.BooleanVar()
        add_screenshots_check = ttk.Checkbutton(root, variable=add_screenshots_var)
        add_screenshots_var.set(config["DEFAULT"].get("add_screenshots", True))
        add_screenshots_check.grid(row=12, column=1)

        make_cpu_mem_comparisions_label = ttk.Label(root, text="Add Memory/CPU compaarisions")
        make_cpu_mem_comparisions_label.grid(row=13, column=0)
        make_cpu_mem_comparisions_var = tk.BooleanVar()
        make_cpu_mem_comparisions_check = ttk.Checkbutton(root, variable=make_cpu_mem_comparisions_var)
        make_cpu_mem_comparisions_var.set(config["DEFAULT"].get("make_cpu_mem_comparisions", True))
        make_cpu_mem_comparisions_check.grid(row=13, column=1)

        #submit button
        submit_button = ttk.Button(root, text="Generate", command=submit)
        submit_button.grid(row=15, column=1)

        # Cancel Button
        cancel_button = ttk.Button(root, text="Cancel", command=cancel)
        cancel_button.grid(row=15, column=0)

        root.mainloop()
        root.quit()
        return details


    except Exception as e:
        print(str(e))
        print("Looks like tkinter canvas is having an issue, do you want to continue with these details?")

        
        nodes_file_name="s1_nodes.json"
        details = {
            "load_type": 'SingleCustomer',
            "start_time_str": "2023-08-12 23:08",
            "load_time_in_hrs": 10,
            "sprint": "138",
            "build": "138000",
            "prev_sprint": "137",
            "start_margin": 10,
            "end_margin": 10,
            "prom_con_obj":PrometheusConnector(nodes_file_name=nodes_file_name)     ,
            "show_gb_cores": False,
            "add_disk_space_usage":True,
            "add_screenshots":True,
            "add_kafka_topics":True,
            "make_cpu_mem_comparisions":True,
        }
        print("nodes_file_name : " + nodes_file_name)
        for key,val in details.items():
            print(f"{key} : {val}")
        
        user_input = input("Select yes to continue, select no to enter new details ... ").strip().lower()
        if user_input == "yes":
            print("Continuing ...")
            return details
        elif user_input == "no":
            print("Please enter your details manually to proceed...(use above details as reference)")
            nodes_file_name = input("nodes file name : ").strip()
            for key in details:
                if key!="prom_con_obj":
                    if type(details[key]) == int:
                        details[key] = int(input(f"Enter {key} :").strip())
                    elif type(details[key]) == str:
                        details[key] = str(input(f"Enter {key} :").strip())
                    elif type(details[key]) == bool:
                        details[key] = bool(input(f"Enter {key} :").strip())

            return details
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            return None





if __name__ == "__main__":
    details = create_input_form()
    print(details)  # Print the details to verify that they are read from the configuration