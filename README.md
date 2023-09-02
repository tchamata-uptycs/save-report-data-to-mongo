# To generate a load report

step 1 : Login to the remote node

step 2: Make sure "<your_stack>_nodes.json" file is present in "../LoadTest-Report-Automation/config" .

step 3: If your stack file is not present, create a new one with name <your_stack>_nodes.json , and enter the details(look at any other stack json as reference) . Do not enter the node-specific details, i.e details until the key "monitoring_node" is sufficient, the remaining data will be fetched and updated automatically.

step 4: Now, run "../LoadTest-Report-Automation/scripts/main.py" and enter the required details. The generated report will be saved at "../LoadTest-Report-Automation/generated_reports/<sprint>/<load_type>"

NOTE : The ip_address and the hostname mappings for your stack must be present in /etc/hosts file.

