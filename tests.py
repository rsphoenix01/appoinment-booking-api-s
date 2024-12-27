from app.db import get_db

# Test the connection
try:
    with get_db() as db:
        # Try to ping the database
        db.command('ping')
        print("Successfully connected to MongoDB!")
        
        # Optional: Print list of collections
        print("Collections in database:", db.list_collection_names())
except Exception as e:
    print("Failed to connect to MongoDB:")
    print(e)