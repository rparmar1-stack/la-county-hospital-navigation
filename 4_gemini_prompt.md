# Gemini Validation Prompt

## Prompt to Use When Testing with Gemini

Attach all 3 markdown files and paste this prompt into Gemini:

---

**PROMPT:**

```
I am providing three Markdown documentation files for a project called the
"LA County Real-Time Hospital Vacancy & Navigation System."

Your task is to regenerate the full working application from these documents alone.

Please generate the following files:

1. backend/models.py — SQLAlchemy models for Hospital, CapacityLog, Admin tables
2. backend/database.py — DB init with 30 real LA County hospitals seeded with realistic data
3. backend/agent.py — Claude AI recommendation agent using haversine distance + specialty matching
4. backend/simulator.py — Async background task that fluctuates hospital capacity every 30 seconds
5. backend/main.py — FastAPI app with:
   - GET /api/hospitals (all hospitals, public)
   - GET /api/hospitals/{id} (single hospital)
   - PUT /api/hospitals/{id}/capacity (JWT protected)
   - POST /api/recommend (AI recommendation, takes symptoms + lat/lng)
   - GET /api/analytics (JWT protected system stats)
   - POST /api/auth/login (JWT)
6. frontend/index.html — Single-file app using React + Leaflet.js (from CDN, no build) with:
   - Interactive LA County map with color-coded hospital markers (green/yellow/red)
   - Sidebar with hospital list, bed availability bars, status filters
   - AI recommendation panel with symptom input
   - Hospital detail modal with directions link
   - Admin analytics panel

Stack: Python/FastAPI backend, SQLite database, Anthropic claude-sonnet-4-6 for AI,
Leaflet.js + OpenStreetMap for maps (free, no API key needed), React from CDN.
```

---

## Running the Application

**Backend:**
```bash
cd backend
pip install fastapi uvicorn sqlalchemy passlib python-jose anthropic python-dotenv
# Create .env with ANTHROPIC_API_KEY=your_key
uvicorn main:app --reload --port 8000
```

**Frontend:**
- Just open `frontend/index.html` in a browser
- No build step needed

**Default admin login:** admin / admin123

## Key Features to Highlight in Email
- 30 real LA County hospitals with actual addresses and coordinates
- Real-time capacity simulation (updates every 30 seconds)
- AI agent routes patients based on symptoms + distance + specialty
- Color-coded live map (🟢 available, 🟡 limited, 🔴 full)
- One-click Google Maps directions from any hospital
- Socially impactful — directly relevant to LA County emergency services
