from fastapi import FastAPI
from app.routes import auth, available, appointments
from app.db import get_db  # Assuming get_db handles the MongoDB connection setup

application = FastAPI()

# Register the routes
application.include_router(auth.router)
application.include_router(available.router)
application.include_router(appointments.router)

# If you're using MongoDB, you don't need to run `Base.metadata.create_all(bind=engine)`
# Remove that line, as it relates to SQLAlchemy and wouldn't be needed for MongoDB.





