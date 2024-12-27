from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from datetime import timedelta
import traceback
from contextlib import contextmanager
from app.db import get_db
from app.models import User  # Import the User model from models.py

# Define FastAPI router
router = APIRouter()

# ... rest of the code remains the same (get_db function, Settings model, get_config function)

# Route to test token validation (unchanged)
# ...

# Route to register a new user
@router.post("/register")
async def register_user(user: User, db=Depends(get_db)): 
    try:
        # Check if the username already exists
        existing_user = db["users"].find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Insert the new user (convert Pydantic model to dictionary)
        result = db["users"].insert_one(user.dict()) 
        user_data = user.dict()
        user_data["_id"] = str(result.inserted_id) 

        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

# Route to log in a user
@router.post("/login")
def login_user(user: User, db=Depends(get_db), Authorize: AuthJWT = Depends()): 
    users_collection = db["users"]  # Access the 'users' collection

    # Fetch user by username
    found_user = users_collection.find_one({"username": user.username})
    if not found_user or found_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT with user details
    access_token = Authorize.create_access_token(
        subject=str(found_user["_id"]),  # Use MongoDB ObjectId as subject
        user_claims={"role": found_user["role"]},
        expires_time=timedelta(hours=1)  # Token expires after 1 hour
    )

    return {
        "access_token": access_token,
        "message": "Login successful",
        "role": found_user["role"]  # Return user role
    }