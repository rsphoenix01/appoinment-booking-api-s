Student-Professor Appointment Management System
Overview
A backend service for managing professor availability and student appointments. Built using FastAPI, SQLAlchemy, and JWT authentication, it ensures a seamless appointment management process.
________________


How to Run
Prerequisites
* Python 3.10+


* SQLite 
Steps to Install and Run




2.)Install Dependencies:

fastapi==0.95.2         # Framework for building the API
uvicorn==0.22.0         # ASGI server for running the FastAPI application
sqlalchemy==2.0.21      # ORM for database interaction
pydantic==1.10.12       # Data validation and settings management




pytest==7.4.0           # For writing and running tests
pytest-asyncio==0.21.0  # Adds asyncio support to pytest
httpx==0.24.1           # HTTP client for making requests (used in testing)






3.) Start the Application from the root directory

         uvicorn app.main:app --reload


Access the API Docs: Open http://127.0.0.1:8000/docs in your browser.

Testing
Install Testing Dependencies
pip install pytest pytest-asyncio


Run from the root directory
pytest