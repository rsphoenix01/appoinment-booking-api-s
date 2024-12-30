from pymongo import MongoClient
from dotenv import load_dotenv
import os
from contextlib import contextmanager

# Load environment variables from the .env file
load_dotenv()

# Retrieve the MongoDB URI from the environment variables
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

# Create a context manager to handle MongoDB connection
# in app/db.py



# Get the path to the project root directory (where global-bundle.pem is)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_PATH = os.path.join(PROJECT_ROOT, 'global-bundle.pem')
print(CERT_PATH)


def get_db():
    client = MongoClient(
        "mongodb+srv://mroshanabbas1205:9b3Tsl9TpXgjzJWS@cluster0.cjml3.mongodb.net/"
         
    )
    try:
        db = client["appointments-system"]
        yield db
    finally:
        client.close()