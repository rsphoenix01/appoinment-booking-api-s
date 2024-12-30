from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Literal, Optional

class ObjectIdStr(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str):
            try:
                return ObjectId(value)
            except Exception:
                raise ValueError(f"Value '{value}' is not a valid ObjectId string")
        raise ValueError(f"Value '{value}' is not a valid ObjectId")

class User(BaseModel):
    username: str
    password: str
    role: Literal["student", "professor"]

    class Config:
        json_encoders = {ObjectId: str}

class Availability(BaseModel):
    professor_id: ObjectIdStr
    start_time: datetime
    end_time: datetime

    class Config:
        json_encoders = {ObjectId: str}

class Appointment(BaseModel):
    professor_id: ObjectIdStr
    student_id: ObjectIdStr
    start_time: str
    end_time: str
    is_canceled: Optional[bool] = False

    class Config:
        json_encoders = {ObjectId: str}
