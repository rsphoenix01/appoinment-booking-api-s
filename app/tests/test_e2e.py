
from datetime import datetime, timedelta




from app.main import application

import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_e2e_flow():
   
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        
        # 1. Student A1 authenticates
        response = await client.post("/login", json={"username": "student1", "password": "password123"})
        assert response.status_code == 200
        student_a1_token = response.json()["access_token"]
        

        # 2. Professor P1 authenticates
        response = await client.post("/login", json={"username": "professor1", "password": "password123"})
        assert response.status_code == 200
        professor_p1_token = response.json()["access_token"]
    

        # 3. Professor P1 specifies available time slots
        headers = {"Authorization": f"Bearer {professor_p1_token}"}
        availability_data = {
        "professor_id": 2,
        "start_time": "2024-06-22T13:00:00",  
        "end_time": "2024-06-22T13:30:00"    
        }

        response = await client.post("/availability", json=availability_data, headers=headers)
        assert response.status_code == 200

        # 4. Student A1 views available time slots for professor p1
        headers = {"Authorization": f"Bearer {student_a1_token}"}
        professor_p1_id = {
            
            "professor_id":2
            
            
        }
        response = await client.post("/getavailability",json = professor_p1_id,  headers={"Authorization": f"Bearer {student_a1_token}"})
        assert response.status_code == 200

        available_slots = response.json()["availability"]
        assert any(
        slot["start_time"] == availability_data["start_time"] and slot["end_time"] == availability_data["end_time"]
        for slot in available_slots
        )

        # 5. Student A1 books an appointment with Professor P1
        appointment_data = {
            "professor_id": 2,
            "student_id": 1,
            "start_time": "2024-06-22T13:10:00",
            "end_time": "2024-06-22T13:15:00",
        }
        response = await client.post("/appointments", json=appointment_data, headers={"Authorization": f"Bearer {student_a1_token}"})
        assert response.status_code == 200
        appointment_id = response.json()["appointment booked successfully for id"]
          # Get the appointment ID

        # 6. Student A2 authenticates
        response = await client.post("/login", json={"username": "student2", "password": "password123"})
        assert response.status_code == 200
        student_a2_token = response.json()["access_token"]
          # Dynamically get student ID

        # 7. Student A2 books an appointment with Professor P1 
        appointment_data = {
            "professor_id": 2,
            "student_id": 3,
            "start_time": "2024-06-22T13:16:00",  
            "end_time": "2024-06-22T13:30:00"   
        }
        response = await client.post("/appointments", json=appointment_data, headers={"Authorization": f"Bearer {student_a2_token}"})
        assert response.status_code == 200 
        assert response.json()

        # 8. Professor P1 cancels the appointment with Student A1 (using PUT request)
        response = await client.put(f"/appointments/{appointment_id}", json={"appointment_id": 2}, headers={"Authorization": f"Bearer {professor_p1_token}"})
        assert response.status_code == 200
        

        # 9. Student A1 checks their appointments a
        response = await client.get(f"/getappointments", headers={"Authorization": f"Bearer {student_a1_token}"})
        assert response.status_code == 200
        assert response.json()
         # The appointment should be canceled

       
