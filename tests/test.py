import requests
import random
import time
from datetime import datetime
import json
import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from backend.surveillance_app.models import Camera, SurveillanceArea

# --- Configuration ---
# IMPORTANT: This must match the address where your Django server is running.
BASE_URL = "http://127.0.0.1:8000"

# Endpoints we configured in the security_app and surveillance_app
HIGH_PRIORITY_ENDPOINT = f"{BASE_URL}/api/security/incidents/"
LOW_PRIORITY_ENDPOINT = f"{BASE_URL}/api/surveillance/area-observations/"

# Mock IDs - You MUST ensure that cameras and areas with these IDs exist
# in your database before running the script.
MOCK_CAMERA_IDS = ['CAM001', 'CAM002', 'CAM003']
MOCK_AREA_IDS = [1, 2]

def setup_test_data():
    """Create test areas and cameras if they don't exist."""
    print("Setting up test data...")

    # Create areas
    area1, created = SurveillanceArea.objects.get_or_create(
        name="Main Entrance",
        defaults={'description': 'Main building entrance area'}
    )
    if created:
        print(f"Created area: {area1}")

    area2, created = SurveillanceArea.objects.get_or_create(
        name="Parking Lot",
        defaults={'description': 'Main parking area'}
    )
    if created:
        print(f"Created area: {area2}")

    # Create cameras
    cameras_data = [
        ('CAM001', area1, 'North wall facing entrance'),
        ('CAM002', area1, 'South wall facing parking'),
        ('CAM003', area2, 'East corner overlooking lot'),
    ]

    for camera_id, area, location in cameras_data:
        camera, created = Camera.objects.get_or_create(
            camera_id=camera_id,
            defaults={
                'area': area,
                'location_description': location,
                'is_online': True
            }
        )
        if created:
            print(f"Created camera: {camera}")

    print("Test data setup complete.")

# --- Helper Function ---

def send_event(url, data, event_type):
    """Sends a POST request and handles the response."""
    
    # We don't need authentication for the AI worker endpoints, but always good practice
    # to define headers.
    headers = {'Content-Type': 'application/json'}
    
    print(f"\n--- Sending {event_type} Event ---")
    print(f"Target URL: {url}")
    print(f"Payload: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"SUCCESS: {event_type} created. Status: {response.status_code}")
            # print(f"Response: {response.json()}")
        else:
            print(f"FAILURE: Status: {response.status_code}")
            print(f"Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to Django server at {BASE_URL}. Is it running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Data Generators ---

def generate_high_priority_incident():
    """Generates a mock payload for a SecurityIncident (HIGH/CRITICAL priority)."""

    # High priority events are WEAPON or CROWD (matching EventType codes)
    event_type_code = random.choice(['WEAPON', 'CROWD'])

    # Critical incidents happen less often
    incident_level = 'CRIT' if random.random() < 0.3 else 'HIGH'

    # Generate appropriate metrics based on event type
    if event_type_code == 'WEAPON':
        metrics = {
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "weapon_type": random.choice(['Handgun', 'Knife', 'Rifle', 'Bat']),
            "detection_box": [
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(400, 600),
                random.randint(400, 600)
            ]
        }
    else:  # CROWD
        metrics = {
            "person_count": random.randint(10, 100),
            "density_level": random.choice(['Very High', 'High', 'Medium']),
            "avg_velocity": round(random.uniform(0.5, 3.0), 2)
        }

    return {
        "event_type_code": event_type_code,
        "camera_id": random.choice(MOCK_CAMERA_IDS),
        "incident_level": incident_level,
        "metrics": metrics,
    }

def generate_low_priority_observation():
    """Generates a mock payload for an AreaObservation (UOD/INTRUSION event)."""

    # Low priority events are UOD (Unusual Object Detection) or INTRUSION
    event_type_code = random.choice(['UOD', 'INTRUSION'])

    # Generate a mock evidence path
    evidence_path = f"/snapshots/{event_type_code.lower()}_{int(time.time())}.jpg"

    return {
        "event_type_code": event_type_code,
        "camera_id": random.choice(MOCK_CAMERA_IDS),
        "evidence_path": evidence_path,
        "details": { # Nested ObjectDetail data
            "object_class": random.choice(['person', 'car', 'bag', 'drone']),
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "bounding_box": [
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(400, 600),
                random.randint(400, 600)
            ]
        }
    }


# --- Main Simulation Loop ---

def simulate_worker(duration_seconds=60, min_delay=1, max_delay=3):
    """
    Simulates the AI worker sending random events for a specified duration.
    Events are sent every 1 to 3 seconds.
    """
    start_time = time.time()
    
    print(f"Starting AI Worker simulation for {duration_seconds} seconds...")
    
    event_count = 0
    while (time.time() - start_time) < duration_seconds:
        # 30% chance of a High Priority Incident, 70% chance of a Low Priority Observation
        if random.random() < 0.3:
            # Send High Priority (SecurityIncident)
            data = generate_high_priority_incident()
            send_event(HIGH_PRIORITY_ENDPOINT, data, "HIGH PRIORITY INCIDENT")
        else:
            # Send Low Priority (AreaObservation)
            data = generate_low_priority_observation()
            send_event(LOW_PRIORITY_ENDPOINT, data, "LOW PRIORITY OBSERVATION")
            
        event_count += 1
        
        # Wait a random delay before the next event
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    print(f"\n--- Simulation Complete ---")
    print(f"Total events sent: {event_count}")
    print("Check your database to see the records created!")

if __name__ == "__main__":
    # Setup test data first
    setup_test_data()

    # Run the simulation for 30 seconds
    simulate_worker(duration_seconds=30)
