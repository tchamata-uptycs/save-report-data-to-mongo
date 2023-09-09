import os
import json
from collections import defaultdict
import shutil,socket,paramiko
import concurrent.futures
import pymongo
from bson import ObjectId
from gridfs import GridFS

def save_screenshots_to_mongo(directory_path, grafana_ids, table_ids,collection,inserted_id,db):
    all_shots = os.listdir(directory_path)
    mapping = defaultdict(lambda: defaultdict(lambda: []))
    for shot in all_shots:
        panel_id, n, file_name = shot.split('_')
        panel_id,n = int(panel_id),int(n)
        title, _ = file_name.split('.')
        mapping[panel_id]['title'] = [title]
        mapping[panel_id]['images'].append(shot)
    
    for index, panel in enumerate(grafana_ids):
        if panel in table_ids:
            mapping[panel]['images'].sort(key=lambda s: int(s.split('_')[1]))
        if panel not in mapping:continue
        title = mapping[panel]['title'][0].capitalize()
        print(f'{index+1}:({panel}){title}')            
        fs = GridFS(db)
        filter = {"_id": ObjectId(inserted_id)} 
        collection.update_one(filter, {"$set": {f"charts.{title}": []}})
        for filename in mapping[panel]['images']:     
            image_file_path = os.path.join(directory_path, filename)
            try:
                with open(image_file_path, "rb") as image_file:
                    image_data = image_file.read()
                file_id = fs.put(image_data, filename=f"{title}.png")
                update = {"$push": {f"charts.{title}": file_id}}
                collection.update_one(filter, update)
            except Exception as e:
                print(f"Error processing image {filename}: {e}")
    try:
        shutil.rmtree(directory_path)
        print(f"Folder '{directory_path}' and its contents have been deleted successfully.")
    except Exception as e:
        print(f"Error deleting screenshots folder: {str(e)}")

def extract_node_detail(data,node_type,prom_con_obj):
    port=prom_con_obj.ssh_port
    username = prom_con_obj.abacus_username
    password  = prom_con_obj.abacus_password
    return_dict={}
    for hostname in data[node_type]:
        return_dict[hostname] = {}
        return_dict[hostname]['storage'] = {}
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys() 
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(hostname, port, username, password)
                commands = {"ram" : "free -g | awk '/Mem:/ {print $2}'" , "cores":"lscpu | awk '/^CPU\(s\):/ {print $2}'"}
                for label,command in commands.items():
                    stdin, stdout, stderr = client.exec_command(command)
                    out = stdout.read().decode('utf-8').strip()
                    if out and out!='':
                        return_dict[hostname][label] = out
                    else:
                        print(f"Unable to determine {label} value for {hostname}")
                
                storage_commands = {'root_partition':"df -h | awk '$6 == \"/\" {print $2}'",
                                    'kafka' : "df -h | awk '$6 == \"/data/kafka\" {print $2}'",
                                    'spark' : "df -h | awk '$6 == \"/data/spark\" {print $2}'",
                                    'dn1' : "df -h | awk '$6 == \"/data/dn1\" {print $2}'",
                                    'dn2' : "df -h | awk '$6 == \"/data/dn2\" {print $2}'",
                                    'dn3' : "df -h | awk '$6 == \"/data/dn3\" {print $2}'",
                                    'pg' : "df -h | awk '$6 == \"/pg\" {print $2}'",
                                    'data' : "df -h | awk '$6 == \"/data\" {print $2}'",
                                    'data_prometheus' : "df -h | awk '$6 == \"/data/prometheus\" {print $2}'",
                                    }

                for label,command in storage_commands.items():
                    stdin, stdout, stderr = client.exec_command(command)
                    out = stdout.read().decode('utf-8').strip()
                    if out and out!='':
                        return_dict[hostname]['storage'][label] = out
                    else:
                        print(f"Unable to determine {label} value for {hostname}")

            except Exception as e:
                print(f'ERROR : Unable connect to {hostname}' , e)
            finally:
                client.close()
        except socket.gaierror:
            print(f"Could not resolve {hostname}")
        if 'c2' in hostname:return_dict[hostname]['clst'] = "2"
        else:return_dict[hostname]['clst'] = "1"

    return return_dict

def extract_stack_details(nodes_file_path,prom_con_obj):
    with open(nodes_file_path,'r') as file:
        data = json.load(file)
    
    def extract_node_detail_wrapper(data, node_type, prom_con_obj):
        return extract_node_detail(data, node_type, prom_con_obj)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future1 = executor.submit(extract_node_detail_wrapper, data, 'pnodes', prom_con_obj)
        future2 = executor.submit(extract_node_detail_wrapper, data, 'dnodes', prom_con_obj)
        future3 = executor.submit(extract_node_detail_wrapper, data, 'pgnodes', prom_con_obj)
        future4 = executor.submit(extract_node_detail_wrapper, data, 'monitoring_node', prom_con_obj)
        future5 = executor.submit(extract_node_detail_wrapper, data, 'other_nodes', prom_con_obj)
        completed_futures, _ = concurrent.futures.wait([future1, future2, future3, future4 , future5])
    pnodes = future1.result()
    dnodes = future2.result()
    pgnodes = future3.result()
    monitoring_node = future4.result()
    other_nodes = future5.result()

    data.update(pnodes)
    data.update(dnodes)
    data.update(pgnodes)
    data.update(monitoring_node)
    data.update(other_nodes)

    with open(nodes_file_path,'w') as file:
        json.dump(data,file,indent=4)

def push_data_to_mongo(load_name,load_type,json_path, connection_string,directory_path, grafana_ids, table_ids):
    try:
        client = pymongo.MongoClient(connection_string)
        db=client[load_type+"_LoadTests"]
        collection = db[load_name]
        with open(json_path,'r') as file:
            doc_to_insert=json.load(file)
        inserted_id = collection.insert_one(doc_to_insert).inserted_id
        if grafana_ids is not None:
            save_screenshots_to_mongo(directory_path, grafana_ids, table_ids,collection,inserted_id,db)
        client.close()
        print(f"Document pushed to mongo successfully into database:{load_type}, collection:{load_name} with id {inserted_id}")
    except:
        print(f"ERROR : Failed to insert document into database {load_name}, collection:{load_name}")