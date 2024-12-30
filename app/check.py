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
MONGO_URI ="mongodb+srv://mroshanabbas1205:9b3Tsl9TpXgjzJWS@cluster0.cjml3.mongodb.net/"

test_connection(MONGO_URI)