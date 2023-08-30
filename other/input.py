import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import configparser
import json
from prometeus_utils import PrometheusConnector

stack_details = {}
nodes_file_path = PrometheusConnector().nodes_file_path
with open(nodes_file_path, 'r') as file:
    stack_details = json.load(file)

stack = stack_details.get("stack", "")

# Initialize the configuration
config = configparser.ConfigParser()
config.read("config.ini")

# Define input field labels and their default values
input_fields = [
    ("Load Type", "load_type" , "SingleCustomer"),
    ("Start Time", "start_time_str", "2023-08-11 23:08"),
    ("Load Time (hrs)", "load_time_in_hrs" , 10),
    ("Sprint", "sprint", "137"),
    ("Previous Sprint", "prev_sprint" , "136"),
    ("Build", "build" , "137006"),
    ("Start Margin", "start_margin" , 10),
    ("End Margin", "end_margin" ,10),
    ("Show GB Cores", "show_gb_cores" ,False),
    ("Table IDs (comma-separated)", "table_ids", "78,80,82")
]

# Create a dictionary to store the user input
user_input = {}

def create_input_form():
    def cancel():
        root.quit()

    def submit():
        global user_input

        # Update the user_input dictionary with the values from the entry fields
        for label,var, default_value in input_fields:
            user_input[var] = entry_vars[label].get()

        # Display a confirmation dialog
        confirm_message = f"Are you sure that the details mentioned are correct for generating a report for stack {stack} ?"
        confirm = messagebox.askokcancel("Confirmation", confirm_message)

        if confirm:
            root.quit()

    def select_date():
        date_str = simpledialog.askstring("Input", "Enter Start Date (YYYY-MM-DD HH:MM)")
        if date_str:
            entry_vars["Start Time"].set(date_str)

    root = tk.Tk()
    root.title("Input Form")

    entry_vars = {}  # Dictionary to store entry variables

    # Create input fields using for loop
    for row, (label,var, default_value) in enumerate(input_fields):
        label_widget = ttk.Label(root, text=label)
        label_widget.grid(row=row, column=0)

        if isinstance(default_value, bool):
            entry_var = tk.BooleanVar(value=default_value)
        elif isinstance(default_value, int):
            entry_var = tk.IntVar(value=default_value)
        else:
            entry_var = tk.StringVar(value=default_value)

        entry_vars[label] = entry_var

        if label == "Load Type":
            entry_widget = ttk.Combobox(root, textvariable=entry_var, values=['ControlPlane', 'SingleCustomer', 'MultiCustomer', 'CombinedLoad'], state="readonly")
        else:
            entry_widget = ttk.Entry(root, textvariable=entry_var)

        entry_widget.grid(row=row, column=1)

        if label == "Start Time":
            date_picker_button = ttk.Button(root, text="Pick Date", command=select_date)
            date_picker_button.grid(row=row, column=2)

    submit_button = ttk.Button(root, text="Submit", command=submit)
    submit_button.grid(row=len(input_fields), column=1)

    # Cancel Button
    cancel_button = ttk.Button(root, text="Cancel", command=cancel)
    cancel_button.grid(row=len(input_fields), column=0)

    root.mainloop()
    # Return user input as a dictionary
    return user_input

if __name__ == "__main__":
    details = create_input_form()
    print(details)  # Print the details to verify that they are read from the configuration
