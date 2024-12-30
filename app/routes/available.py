from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from fastapi_jwt_auth import AuthJWT
from datetime import datetime
from app.models import Availability, User
from contextlib import contextmanager
import traceback
from app.db import get_db
from bson import ObjectId 

router = APIRouter()

# MongoDB Connection



# Route to create availability
@router.post("/availability")
def create_availability(
    availability_data: Availability,
    db=Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    try:
        # JWT validation
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()  # JWT subject is a string
        raw_jwt = Authorize.get_raw_jwt()
        user_role = raw_jwt.get("role")

        # Role validation
        if user_role != "professor":
            raise HTTPException(status_code=403, detail="Only professors can add availability")

        # Convert user_id to ObjectId for MongoDB query
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        user_object_id = ObjectId(user_id)

        # Ownership validation
        if availability_data.professor_id != user_object_id:
            raise HTTPException(status_code=403, detail="You cannot set availability for another professor!")

        # Check for overlapping slots
        availability_collection = db["availability"]
        overlapping_slots = availability_collection.find({
            "professor_id": user_object_id,
            "$or": [
                {"start_time": {"$lt": availability_data.end_time}, "end_time": {"$gt": availability_data.start_time}}
            ]
        })

        # Use len(list()) to count the number of overlapping slots
        if len(list(overlapping_slots)) > 0:
            conflict_details = [
                {"start_time": slot["start_time"], "end_time": slot["end_time"]}
                for slot in overlapping_slots
            ]
            raise HTTPException(
                status_code=409,
                detail={"message": "Time slot conflicts found", "conflicts": conflict_details}
            )

        # Insert availability
        new_availability = {
            "professor_id": user_object_id,  # Use ObjectId in MongoDB
            "start_time": availability_data.start_time,
            "end_time": availability_data.end_time,
        }
        result = availability_collection.insert_one(new_availability)

        return {
            "message": "Availability successfully added",
            "availability": {
                "id": str(result.inserted_id),
                "start_time": availability_data.start_time,
                "end_time": availability_data.end_time,
                "professor_id": user_id  # Return as string for consistency
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/getavailability")
def get_availability(
    professor_id: str,
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db)
):
    try:
        # JWT validation
        Authorize.jwt_required()
        raw_jwt = Authorize.get_raw_jwt()
        user_role = raw_jwt.get("role")

        if user_role != "student":
            raise HTTPException(status_code=403, detail="Only students can view availability")

        # Convert professor_id to ObjectId
        if not ObjectId.is_valid(professor_id):
            raise HTTPException(status_code=400, detail="Invalid professor ID format")

        professor_object_id = ObjectId(professor_id)

        # Check professor existence
        users_collection = db["users"]
        professor = users_collection.find_one({"_id": professor_object_id})
        if not professor:
            raise HTTPException(status_code=404, detail="Professor not found")

        # Fetch availability slots
        availability_collection = db["availability"]
        availability_slots = list(availability_collection.find({"professor_id": professor_object_id}))

        if not availability_slots:
            raise HTTPException(status_code=404, detail="No availability found for the professor")

        # Format response
        availability_data = [
            {
                "availability_id": str(slot["_id"]),
                "professor_id": str(slot["professor_id"]),  # Convert ObjectId to string
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
            }
            for slot in availability_slots
        ]

        return {"availability": availability_data}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
