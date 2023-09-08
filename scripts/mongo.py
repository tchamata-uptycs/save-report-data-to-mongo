import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017")
dbs = client.list_database_names()
db=client['Osquery_LoadTests']
multi_customer_collection = db['MultiCustomer']

# to get cpu usage of a particular app in a sprint

a = multi_customer_collection.find({"details.sprint" : "137"} , {"container_wise_memory.Container.tls":1})
for i in a:
    print(i)


# to get cpu usage of a particular app in all sprints
# app = "tls"
# a = multi_customer_collection.find( {}, {"details.sprint":1, f"container_wise_memory.Container.{app}":1})
# for i in a:
#     print(i)

# a = multi_customer_collection.find( {}, {"kafka_topics":1})
# for i in a:
#     print(i)

# a = multi_customer_collection.find( {"details.Total assets":"80K Control Plane +15K Multi customer"}, {"kafka_topics":1})
# for i in a:
#     print(i)

documents_with_same_sprint = multi_customer_collection.find({"details.sprint":139})

documents_with_same_sprint = multi_customer_collection.find({"details.sprint":139} , {"details.run":1})
# print(list(documents_with_same_sprint))
max_run = 0
for i in documents_with_same_sprint :
    max_run = max(i['details']['run'] , max_run)
