from pymongo import MongoClient
from gridfs import GridFS
import os
from bson import Binary,ObjectId

# Initialize the MongoDB client and connect to your database
client = MongoClient('mongodb://localhost:27017')
db = client['CloudQuery_LoadTests']

# Create a GridFS instance using the database
fs = GridFS(db)

# Specify the file_id of the file you want to retrieve
file_id = ObjectId("64fc8c2a5ddb8fd9cf622de6")  # Replace 'your_file_id' with the actual file_id

# Get the file from GridFS
file = fs.get(file_id)

# Specify the path where you want to save the retrieved file
output_file_path = 'path_to_save_retrieved_file.jpg'  # Replace with your desired file path

# Save the retrieved file to the local file system
with open(output_file_path, 'wb') as output_file:
    output_file.write(file.read())

print(f"File saved to {output_file_path}")
