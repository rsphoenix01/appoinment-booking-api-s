from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from fastapi_jwt_auth import AuthJWT
from datetime import datetime
from app.schemas import AvailabilityCreate, UserCreate
from contextlib import contextmanager
import traceback
from app.db import get_db

router = APIRouter()

# MongoDB Connection



# Route to create availability
@router.post("/availability")
def create_availability(
    availability_data: AvailabilityCreate,
    db=Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    try:
        # JWT validation
        Authorize.jwt_required()
        user_id = int(Authorize.get_jwt_subject())
        raw_jwt = Authorize.get_raw_jwt()
        user_role = raw_jwt.get("role")

        # Role and ownership validation
        if user_role != "professor":
            raise HTTPException(status_code=403, detail="Only professors can add availability")

        if availability_data.professor_id != user_id:
            raise HTTPException(status_code=403, detail="You cannot set availability for another professor!")

        # Parse and validate times
        try:
            start_time = datetime.fromisoformat(availability_data.start_time)
            end_time = datetime.fromisoformat(availability_data.end_time)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")

        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Start time should be before end time")

        # Check for overlapping slots
        availability_collection = db["availability"]
        overlapping_slots = availability_collection.find({
            "professor_id": user_id,
            "$or": [
                {"start_time": {"$lt": availability_data.end_time}, "end_time": {"$gt": availability_data.start_time}}
            ]
        })

        if overlapping_slots.count() > 0:
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
            "professor_id": user_id,
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
                "professor_id": user_id
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# Route to get availability for a professor
@router.post("/getavailability")
def get_availability(
    professor_id: int,
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

        # Check professor existence
        users_collection = db["users"]
        professor = users_collection.find_one({"id": professor_id})
        if not professor:
            raise HTTPException(status_code=404, detail="Professor not found")

        # Fetch availability slots
        availability_collection = db["availability"]
        availability_slots = list(availability_collection.find({"professor_id": professor_id}))

        if not availability_slots:
            raise HTTPException(status_code=404, detail="No availability found for the professor")

        # Format response
        availability_data = [
            {
                "availability_id": str(slot["_id"]),
                "professor_id": slot["professor_id"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
            }
            for slot in availability_slots
        ]

        return {"availability": availability_data}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
