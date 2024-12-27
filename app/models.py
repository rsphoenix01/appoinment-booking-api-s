from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class User(BaseModel):
    username: str
   
    password: str
    role: str = Field("student", choices=["student", "professor"])

class Availability(BaseModel):
    professor_id: int
    start_time: datetime
    end_time: datetime

class Appointment(BaseModel):
    professor_id: int
    student_id: int
    start_time: datetime
    end_time: datetime
    is_canceled: bool = False