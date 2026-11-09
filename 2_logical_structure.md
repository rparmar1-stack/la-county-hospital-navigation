# Logical Structure Document: LA County Hospital Vacancy & Navigation System

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Leaflet.js)            │
│   Interactive Map  |  Hospital Cards  |  AI Recommendation   │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼───────────────────────────────┐
│                    BACKEND (FastAPI / Python)                 │
│   Hospital API  |  AI Agent  |  Analytics  |  Auth Service   │
└───────┬──────────────────────┬──────────────────────┬────────┘
        │                      │                      │
┌───────▼──────┐   ┌───────────▼──────────┐  ┌───────▼──────┐
│  SQLite DB   │   │   Claude AI API       │  │  OpenStreet  │
│  (Hospitals, │   │   (Wait time pred.    │  │  Map Tiles   │
│   Capacity,  │   │    + Recommendation   │  │  (Free Maps) │
│   Analytics) │   │    Agent)             │  └──────────────┘
└──────────────┘   └──────────────────────┘
```

---

## Data Flow Diagrams

### Flow 1: User Opens Map

```
User opens app
      │
      ▼
Frontend loads → GET /api/hospitals
      │
      ▼
Backend queries DB → returns all LA hospitals with:
  - name, address, lat/lng
  - bed counts (ER, ICU, General, Pediatric)
  - current occupancy percentages
  - specialty tags
  - status (AVAILABLE / LIMITED / FULL / DIVERSION)
      │
      ▼
Map renders with color-coded markers:
  🟢 Green  = < 70% capacity
  🟡 Yellow = 70–90% capacity
  🔴 Red    = > 90% capacity / Diversion
```

### Flow 2: User Requests AI Recommendation

```
User enters: symptoms + current location
      │
      ▼
POST /api/recommend
      │
      ▼
AI Agent receives:
  - User symptoms/condition
  - User coordinates
  - All hospital data + capacity
      │
      ▼
AI Agent reasons:
  1. Identifies required specialty (trauma / cardiac / general)
  2. Filters hospitals with capacity
  3. Weighs distance vs. availability vs. specialty match
  4. Returns top 3 recommendations with reasoning
      │
      ▼
Frontend displays ranked hospital cards with:
  - Match score
  - Estimated wait time
  - One-click directions link
```

### Flow 3: Hospital Updates Capacity

```
Hospital admin logs in → PUT /api/hospitals/{id}/capacity
      │
      ▼
Backend validates JWT → updates DB record
      │
      ▼
New capacity data available on next map refresh (30s polling)
```

---

## Database Schema

### Table: hospitals
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Hospital full name |
| address | TEXT | Street address |
| city | TEXT | City (all LA County) |
| latitude | FLOAT | GPS latitude |
| longitude | FLOAT | GPS longitude |
| phone | TEXT | Main phone number |
| er_beds_total | INTEGER | Total ER beds |
| er_beds_available | INTEGER | Current available ER beds |
| icu_beds_total | INTEGER | Total ICU beds |
| icu_beds_available | INTEGER | Current available ICU beds |
| general_beds_total | INTEGER | Total general beds |
| general_beds_available | INTEGER | Available general beds |
| pediatric_beds_total | INTEGER | Total pediatric beds |
| pediatric_beds_available | INTEGER | Available pediatric beds |
| specialties | TEXT | JSON array of specialties |
| status | TEXT | AVAILABLE / LIMITED / FULL / DIVERSION |
| wait_time_minutes | INTEGER | Current estimated ER wait |
| last_updated | DATETIME | Last capacity update |
| is_trauma_center | BOOLEAN | Level I/II trauma designation |

### Table: capacity_logs
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| hospital_id | INTEGER FK | Reference to hospital |
| er_available | INTEGER | ER snapshot |
| icu_available | INTEGER | ICU snapshot |
| status | TEXT | Status at time of log |
| logged_at | DATETIME | Timestamp |

### Table: admins
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| username | TEXT UNIQUE | Login username |
| hashed_password | TEXT | Bcrypt hash |
| hospital_id | INTEGER FK | Which hospital they manage |

---

## Component Breakdown

### Frontend
- `App.jsx` — Main app, routing, map state
- `HospitalMap.jsx` — Leaflet.js interactive map with color markers
- `HospitalCard.jsx` — Expandable hospital info panel
- `AIRecommendPanel.jsx` — Symptom input + AI recommendation display
- `CapacityBar.jsx` — Visual bed availability bar component
- `FilterPanel.jsx` — Filter by specialty, status, distance
- `AdminPanel.jsx` — Hospital admin capacity updater

### Backend
- `main.py` — FastAPI app, routes
- `models.py` — SQLAlchemy ORM models
- `database.py` — DB init + LA hospital seed data (30 real hospitals)
- `agent.py` — Claude AI recommendation agent
- `simulator.py` — Background task: randomly fluctuates capacity to simulate real-time data

---

## Security Design
- JWT auth for hospital admin updates
- Public read-only access for map and hospital data
- Rate limiting: 30 requests/minute on AI recommendation endpoint
- All API keys in environment variables
