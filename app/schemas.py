from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class UserCreate(BaseModel):
    password: str
    username: str
    role: str

class AvailabilityCreate(BaseModel):
    professor_id: int  # Add professor_id in the Pydantic model
    start_time: str
    end_time: str

class AppointmentCreate(BaseModel):
    professor_id: int
    student_id: int
    start_time: str
    end_time: str
