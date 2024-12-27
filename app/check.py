from pymongo import MongoClient
from dotenv import load_dotenv
import os
MONGO_URI = os.getenv("MONGO_URI")
def test_connection(MONGO_URI):
    try:
        client = MongoClient(MONGO_URI) 
        client.server_info()  # This will raise an exception if the connection fails
        print("Connection to DocumentDB successful!")
    except Exception as e:
        print(f"Connection failed: {e}")

# Replace with your actual MongoDB URI
MONGO_URI = "mongodb://rsphoenix01:roshan2001@docdb-2024-12-25-19-53-23.cluster-cpewq2y240fa.ap-south-1.docdb.amazonaws.com:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"


test_connection(MONGO_URI)