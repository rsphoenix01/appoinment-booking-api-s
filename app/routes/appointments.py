from fastapi import APIRouter, Depends, HTTPException
from app.models import Appointment
from app.db import get_db  # MongoDB connection
from datetime import datetime
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from contextlib import contextmanager
import logging
import os
import pytz
from app.db import get_db


# Set up logging
logger = logging.getLogger(__name__)

# MongoDB helper for appointments


# JWT Settings
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "admin123")  # Use environment variable for JWT secret key
    authjwt_algorithm: str = "HS256"

# Load the configuration for JWT
@AuthJWT.load_config
def get_config():
    return Settings()

# APIRouter for Appointment-related routes
router = APIRouter()

# Appointment Booking Route
@router.post("/appointments")
def book_appointment(
    appointment: Appointment,
    db: MongoClient = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    try:
        # Step 1: Ensure the user is authorized
        Authorize.jwt_required()
        student_id = str(Authorize.get_jwt_subject())  # JWT subject is the student ID
        user_role = Authorize.get_raw_jwt().get("role")
        print(student_id)

        if user_role != "student":
            raise HTTPException(status_code=403, detail="Only students can book appointments")

        # Step 2: Verify the professor exists
        professor = db["users"].find_one({"_id": ObjectId(appointment.professor_id), "role": "professor"})
        if not professor:
            raise HTTPException(status_code=404, detail="Professor not found")

        # Step 3: Ensure the student is booking for themselves
        if student_id != str(appointment.student_id):
            raise HTTPException(status_code=403, detail="You can only book appointments for yourself")

        # Step 4: Validate the time slot provided
        try:
            start_time = datetime.fromisoformat(appointment.start_time)
            end_time = datetime.fromisoformat(appointment.end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format for start_time or end_time")

        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Start time must be earlier than end time")

        # Step 5: Check professor's availability for the requested slot
        available_slots = list(db["availability"].find({"professor_id": appointment.professor_id}))

        # Ensure that the requested time slot is fully covered by one of the professor's availability slots
        slot_found = any(
            slot["start_time"] <= start_time and slot["end_time"] >= end_time for slot in available_slots
        )
        if not slot_found:
            raise HTTPException(
                status_code=409,
                detail="Requested time is outside the professor's availability slots. Available slots are: " +
                       ", ".join([f"{slot['start_time']} - {slot['end_time']}" for slot in available_slots])
            )

        # Step 6: Ensure no overlapping appointments
        existing_appointments = db["appointments"].find_one({
            "professor_id": appointment.professor_id,
            "start_time": {"$lt": end_time},
            "end_time": {"$gt": start_time},
            "is_canceled": False
        })
        if existing_appointments:
            raise HTTPException(status_code=409, detail="There is already an existing appointment during this time slot.")

        # Step 7: Save the appointment if all checks pass
        new_appointment = {
            "professor_id": appointment.professor_id,
            "student_id": appointment.student_id,
            "start_time": start_time,
            "end_time": end_time,
            "is_canceled": False
        }
        result = db["appointments"].insert_one(new_appointment)

        # Step 8: Update professor's availability
        for slot in available_slots:
            if slot["start_time"] == start_time and slot["end_time"] == end_time:
                # Remove the exact match slot (fully booked)
                db["availabily"].delete_one({"_id": slot["_id"]})
            elif start_time > slot["start_time"] and end_time < slot["end_time"]:
                # Case 1: Split the availability into two parts
                new_slot1 = {
                    "professor_id": appointment.professor_id,
                    "start_time": slot["start_time"],
                    "end_time": start_time
                }
                new_slot2 = {
                    "professor_id": appointment.professor_id,
                    "start_time": end_time,
                    "end_time": slot["end_time"]
                }
                db["availability"].insert_one(new_slot1)
                db["availability"].insert_one(new_slot2)

                # Delete the original slot after creating the two new slots
                db["availability"].delete_one({"_id": slot["_id"]})
            elif start_time == slot["start_time"]:
                # Case 2: Shrink the slot to start after the appointment
                db["availability"].update_one(
                    {"_id": slot["_id"]}, {"$set": {"start_time": end_time}}
                )
            elif end_time == slot["end_time"]:
                # Case 3: Shrink the slot to end before the appointment
                db["availability"].update_one(
                    {"_id": slot["_id"]}, {"$set": {"end_time": start_time}}
                )

        logger.info(f"Appointment booked successfully for student {appointment.student_id} with professor {appointment.professor_id}")

        return {"message": "Appointment booked successfully", "appointment_id": str(result.inserted_id)}

    except Exception as error:
        logger.error(f"Unexpected error occurred: {str(error)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(error)}")

# Cancel Appointment Route
@router.put("/appointments/{appointmentid}")
def cancel_appointment(
    appointmentid: str,
    db: MongoClient = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    try:
        # Require JWT authorization
        Authorize.jwt_required()

        # Extract professor ID and role from the JWT
        professor_id = str(Authorize.get_jwt_subject())  # JWT subject is the professor ID
        raw_jwt = Authorize.get_raw_jwt()
        role = raw_jwt.get("role")

        # Ensure the user is a professor
        if role != "professor":
            raise HTTPException(
                status_code=403, detail="Only professors can cancel appointments"
            )

        # Fetch the appointment from the database
        appointment = db["appointments"].find_one({"_id": ObjectId(appointmentid)})

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Ensure the professor owns the appointment
        if appointment["professor_id"] != professor_id:
            raise HTTPException(
                status_code=403, detail="You can only cancel your own appointments"
            )

        # Update the appointment status
        db["appointments"].update_one({"_id": ObjectId(appointmentid)}, {"$set": {"is_canceled": True}})

        logger.info(f"Appointment {appointmentid} canceled by professor {professor_id}")

        return {
            "message": "Appointment canceled successfully",
            "appointment_id": appointmentid,
            "is_canceled": True,
        }

    except Exception as error:
        logger.error(f"Error occurred while canceling appointment {appointmentid}: {str(error)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(error)}")

# Get Appointments Route
@router.get("/getappointments")
def get_appointments(Authorize: AuthJWT = Depends(), db: MongoClient = Depends(get_db)):
    # Ensure the user is authorized
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    raw_jwt = Authorize.get_raw_jwt()
    role = raw_jwt.get("role")

    # Convert user_id to ObjectId for database query
    try:
        userid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Fetch appointments based on role
    if role == "professor":
        appointments = list(db["appointments"].find({
            "professor_id": userid,
            "is_canceled": False
        }))
    elif role == "student":
        appointments = list(db["appointments"].find({
            "student_id": userid,
            "is_canceled": False
        }))
    else:
        raise HTTPException(status_code=403, detail="Unauthorized role")

    # If no appointments found, return an empty list
    if not appointments:
        return {"appointments": []}

    # Serialize the appointment data
    appointment_data = []
    for appointment in appointments:
        try:
            appointment_data.append({
                "appointment_id": str(appointment["_id"]),
                "student_id": str(appointment["student_id"]),  # Convert ObjectId to string
                "professor_id": str(appointment["professor_id"]),  # Convert ObjectId to string
                "start_time": appointment["start_time"].isoformat() if isinstance(appointment["start_time"], datetime) else appointment["start_time"],
                "end_time": appointment["end_time"].isoformat() if isinstance(appointment["end_time"], datetime) else appointment["end_time"],
                "is_canceled": appointment["is_canceled"]
            })
        except KeyError as e:
            raise HTTPException(status_code=500, detail=f"Missing key in appointment data: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing appointment data: {str(e)}")

    # Return the serialized appointment data
    return {"appointments": appointment_data}
