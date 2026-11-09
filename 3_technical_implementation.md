# Technical Implementation Guide: LA County Hospital Vacancy & Navigation System

## Prerequisites

- Python 3.11+
- Node.js 18+ (optional, frontend is single HTML file)
- pip installed
- Anthropic API key

---

## Step 1: Project Setup

### 1.1 Directory Structure

```
la-hospital-system/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── agent.py
│   ├── simulator.py
│   └── .env
└── frontend/
    └── index.html
```

### 1.2 Install Backend Dependencies

```bash
cd backend
pip install fastapi uvicorn sqlalchemy passlib python-jose anthropic python-dotenv
```

### 1.3 Environment Variables

Create `backend/.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///./la_hospitals.db
```

---

## Step 2: Database Construction

### 2.1 Models (backend/models.py)

Define three SQLAlchemy models:

**Hospital model** — stores all 30 LA County hospitals with:
- Geographic coordinates (latitude, longitude)
- Bed counts per type (ER, ICU, General, Pediatric)
- Current availability counts
- Specialties as JSON array
- Status enum: AVAILABLE, LIMITED, FULL, DIVERSION
- Trauma center flag
- Last updated timestamp

**CapacityLog model** — append-only audit log:
- Foreign key to Hospital
- Snapshot of ER/ICU availability
- Status at time of log
- Auto-timestamp

**Admin model** — hospital administrators:
- Username, bcrypt hashed password
- Foreign key to hospital they manage

### 2.2 Database Initialization (backend/database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Hospital, Admin
import json, os
from passlib.context import CryptContext

engine = create_engine("sqlite:///./la_hospitals.db",
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Hospital).count() == 0:
        seed_hospitals(db)
    if db.query(Admin).count() == 0:
        db.add(Admin(username="admin", hashed_password=pwd_context.hash("admin123"), hospital_id=1))
        db.commit()
    db.close()
```

### 2.3 Seed 30 Real LA County Hospitals

The seed function inserts all major LA County hospitals with real addresses and coordinates:

```python
hospitals = [
    {"name": "Cedars-Sinai Medical Center", "address": "8700 Beverly Blvd",
     "city": "Los Angeles", "latitude": 34.0762, "longitude": -118.3803,
     "er_beds_total": 80, "icu_beds_total": 60, "general_beds_total": 400,
     "pediatric_beds_total": 40, "is_trauma_center": True,
     "specialties": json.dumps(["Cardiac", "Neurology", "Oncology", "Trauma"])},
    {"name": "UCLA Medical Center", ...},
    {"name": "Keck Hospital of USC", ...},
    # ... 27 more hospitals
]
```

Each hospital is seeded with randomized but realistic initial availability (60–95% capacity).

---

## Step 3: AI Recommendation Agent

### 3.1 Agent Design (backend/agent.py)

```python
import anthropic, json, os, math

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

AGENT_SYSTEM_PROMPT = """
You are an emergency medical triage routing agent for LA County.
Given a patient's symptoms/condition and their location, plus a list of nearby hospitals
with real-time bed availability, recommend the TOP 3 best hospitals.

For each recommendation return a JSON array of objects with:
- hospital_id: integer
- hospital_name: string
- match_score: integer 1-100
- reason: one sentence why this hospital is best for this patient
- urgency: LOW / MEDIUM / HIGH / CRITICAL
- recommended_transport: DRIVE_YOURSELF / CALL_911

Return ONLY the JSON array, no other text.
"""

def get_recommendation(symptoms: str, user_lat: float, user_lng: float, hospitals: list) -> list:
    # Build hospital context string
    hospital_context = "\n".join([
        f"ID:{h['id']} | {h['name']} | {h['city']} | "
        f"ER:{h['er_beds_available']}/{h['er_beds_total']} | "
        f"ICU:{h['icu_beds_available']}/{h['icu_beds_total']} | "
        f"Status:{h['status']} | Specialties:{h['specialties']} | "
        f"Trauma:{h['is_trauma_center']} | Distance:{h['distance_miles']:.1f}mi"
        for h in hospitals
    ])

    prompt = f"""
Patient condition: {symptoms}
Patient location: {user_lat}, {user_lng}

Available LA County Hospitals:
{hospital_context}

Recommend the best 3 hospitals for this patient.
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=AGENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.content[0].text)

def haversine_distance(lat1, lng1, lat2, lng2) -> float:
    """Calculate distance in miles between two GPS coordinates."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))
```

---

## Step 4: Capacity Simulator

### 4.1 Background Simulator (backend/simulator.py)

Since real hospital APIs require government access, this module simulates realistic
real-time capacity fluctuations:

```python
import asyncio, random
from database import SessionLocal
from models import Hospital, CapacityLog
from datetime import datetime

async def simulate_capacity_changes():
    """Runs every 30 seconds, randomly fluctuates hospital bed availability."""
    while True:
        await asyncio.sleep(30)
        db = SessionLocal()
        hospitals = db.query(Hospital).all()
        for hospital in hospitals:
            # Simulate ±1-3 bed changes per cycle
            hospital.er_beds_available = max(0, min(
                hospital.er_beds_total,
                hospital.er_beds_available + random.randint(-3, 3)
            ))
            hospital.icu_beds_available = max(0, min(
                hospital.icu_beds_total,
                hospital.icu_beds_available + random.randint(-2, 2)
            ))
            # Recalculate status
            er_pct = hospital.er_beds_available / hospital.er_beds_total
            if er_pct > 0.3:
                hospital.status = "AVAILABLE"
            elif er_pct > 0.1:
                hospital.status = "LIMITED"
            else:
                hospital.status = "FULL"
            hospital.last_updated = datetime.utcnow()
            # Log the change
            db.add(CapacityLog(hospital_id=hospital.id,
                               er_available=hospital.er_beds_available,
                               icu_available=hospital.icu_beds_available,
                               status=hospital.status))
        db.commit()
        db.close()
```

---

## Step 5: Backend API

### 5.1 FastAPI Routes (backend/main.py)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/hospitals | Public | All hospitals with current capacity |
| GET | /api/hospitals/{id} | Public | Single hospital detail |
| PUT | /api/hospitals/{id}/capacity | JWT | Update bed availability |
| POST | /api/recommend | Public | AI hospital recommendation |
| GET | /api/analytics | JWT | System-wide capacity analytics |
| POST | /api/auth/login | Public | Admin JWT login |

**POST /api/recommend payload:**
```json
{
  "symptoms": "chest pain, shortness of breath",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "max_distance_miles": 20
}
```

**Response:**
```json
[
  {
    "hospital_id": 1,
    "hospital_name": "Cedars-Sinai Medical Center",
    "match_score": 95,
    "reason": "Leading cardiac center with available ICU beds, 3.2 miles away",
    "urgency": "HIGH",
    "recommended_transport": "CALL_911"
  }
]
```

---

## Step 6: Frontend (frontend/index.html)

Single HTML file using React + Leaflet.js from CDN. No build step required.

### 6.1 Map Implementation
- Use **Leaflet.js** with OpenStreetMap tiles (free, no API key needed)
- Custom colored circle markers: green/yellow/red based on hospital status
- Popup on marker click: shows bed availability bars + directions link

### 6.2 Key UI Sections
- **Map Panel (70% width):** Interactive LA County map with all hospital markers
- **Side Panel (30% width):**
  - Filter controls (specialty, status, distance)
  - AI Recommendation input (symptom text box)
  - Hospital list sorted by availability
- **Hospital Detail Modal:** Full bed breakdown, wait time, phone, directions

### 6.3 Directions Integration
Generate Google Maps directions URL dynamically:
```javascript
const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}&travelmode=driving`;
window.open(directionsUrl, '_blank');
```

---

## Step 7: Running the Application

### 7.1 Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 7.2 Open Frontend
Simply open `frontend/index.html` in any browser. No build step needed.

### 7.3 Test AI Recommendation
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "severe chest pain radiating to left arm",
    "latitude": 34.0522,
    "longitude": -118.2437,
    "max_distance_miles": 15
  }'
```

Expected: Top 3 cardiac-capable hospitals sorted by match score.

---

## Step 8: Admin Panel Usage

1. Navigate to Admin section in the app
2. Login with `admin` / `admin123`
3. Select your hospital
4. Update bed counts in real time
5. Changes reflect on map within 5 seconds
