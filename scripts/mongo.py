import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017")
dbs = client.list_database_names()
db=client['all_loads']
multi_customer_collection = db['MultiCustomer']

# to get cpu usage of a particular app in a sprint

a = multi_customer_collection.find({"details.sprint" : "137"} , {"container_wise_memory.Container.tls":1})
for i in a:
    print(i)


# to get cpu usage of a particular app in all sprints
app = "tls"
a = multi_customer_collection.find( {}, {"details.sprint":1, f"container_wise_memory.Container.{app}":1})
for i in a:
    print(i)

# a = multi_customer_collection.find( {}, {"kafka_topics":1})
# for i in a:
#     print(i)

# a = multi_customer_collection.find( {"details.Total assets":"80K Control Plane +15K Multi customer"}, {"kafka_topics":1})
# for i in a:
#     print(i)