from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json, os, asyncio

from database import init_db, get_db, SessionLocal
from models import Hospital, CapacityLog, Admin
from agent import get_recommendation, haversine_distance
from simulator import simulate_capacity_changes

app = FastAPI(title="LA County Hospital Vacancy & Navigation System")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SECRET_KEY = os.getenv("SECRET_KEY", "la-hospital-secret-key")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def create_token(username: str):
    return jwt.encode({"sub": username, "exp": datetime.utcnow() + timedelta(hours=8)},
                      SECRET_KEY, algorithm=ALGORITHM)

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin = db.query(Admin).filter(Admin.username == payload.get("sub")).first()
        if not admin: raise HTTPException(status_code=401, detail="Invalid token")
        return admin
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─── Schemas ──────────────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    symptoms: str
    latitude: float
    longitude: float
    max_distance_miles: Optional[float] = 25.0

class CapacityUpdate(BaseModel):
    er_beds_available: Optional[int] = None
    icu_beds_available: Optional[int] = None
    general_beds_available: Optional[int] = None
    wait_time_minutes: Optional[int] = None
    status: Optional[str] = None

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(simulate_capacity_changes(SessionLocal, Hospital, CapacityLog))

# ─── Auth ─────────────────────────────────────────────────────────────────────
@app.post("/api/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form.username).first()
    if not admin or not pwd_context.verify(form.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(admin.username), "token_type": "bearer"}

# ─── Hospital Routes ──────────────────────────────────────────────────────────
def hospital_to_dict(h: Hospital) -> dict:
    return {
        "id": h.id, "name": h.name, "address": h.address, "city": h.city,
        "latitude": h.latitude, "longitude": h.longitude, "phone": h.phone,
        "er_beds_total": h.er_beds_total, "er_beds_available": h.er_beds_available,
        "icu_beds_total": h.icu_beds_total, "icu_beds_available": h.icu_beds_available,
        "general_beds_total": h.general_beds_total, "general_beds_available": h.general_beds_available,
        "pediatric_beds_total": h.pediatric_beds_total, "pediatric_beds_available": h.pediatric_beds_available,
        "specialties": json.loads(h.specialties) if h.specialties else [],
        "status": h.status, "wait_time_minutes": h.wait_time_minutes,
        "is_trauma_center": h.is_trauma_center,
        "last_updated": h.last_updated.isoformat() if h.last_updated else None,
        "er_pct": round((h.er_beds_available / h.er_beds_total * 100) if h.er_beds_total > 0 else 0, 1),
        "icu_pct": round((h.icu_beds_available / h.icu_beds_total * 100) if h.icu_beds_total > 0 else 0, 1),
    }

@app.get("/api/hospitals")
def get_hospitals(db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).order_by(Hospital.name).all()
    return [hospital_to_dict(h) for h in hospitals]

@app.get("/api/hospitals/{hospital_id}")
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not h: raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital_to_dict(h)

@app.put("/api/hospitals/{hospital_id}/capacity")
def update_capacity(hospital_id: int, update: CapacityUpdate,
                    db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    h = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not h: raise HTTPException(status_code=404, detail="Not found")
    if update.er_beds_available is not None: h.er_beds_available = update.er_beds_available
    if update.icu_beds_available is not None: h.icu_beds_available = update.icu_beds_available
    if update.general_beds_available is not None: h.general_beds_available = update.general_beds_available
    if update.wait_time_minutes is not None: h.wait_time_minutes = update.wait_time_minutes
    if update.status: h.status = update.status
    h.last_updated = datetime.utcnow()
    db.add(CapacityLog(hospital_id=h.id, er_available=h.er_beds_available,
                       icu_available=h.icu_beds_available, status=h.status))
    db.commit()
    return {"message": "Capacity updated", "hospital": hospital_to_dict(h)}

# ─── AI Recommendation ────────────────────────────────────────────────────────
@app.post("/api/recommend")
def recommend_hospital(req: RecommendRequest, db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).all()
    hospital_list = [hospital_to_dict(h) for h in hospitals]

    # Filter by distance
    filtered = [
        h for h in hospital_list
        if haversine_distance(req.latitude, req.longitude, h["latitude"], h["longitude"]) <= req.max_distance_miles
    ]
    if not filtered:
        filtered = hospital_list  # Fall back to all if none in range

    recommendations = get_recommendation(req.symptoms, req.latitude, req.longitude, filtered)

    # Enrich recommendations with full hospital data
    hospital_map = {h["id"]: h for h in hospital_list}
    enriched = []
    for rec in recommendations:
        h_data = hospital_map.get(rec.get("hospital_id"), {})
        enriched.append({**rec, **{
            "address": h_data.get("address"),
            "city": h_data.get("city"),
            "latitude": h_data.get("latitude"),
            "longitude": h_data.get("longitude"),
            "phone": h_data.get("phone"),
            "status": h_data.get("status"),
            "wait_time_minutes": h_data.get("wait_time_minutes"),
            "er_beds_available": h_data.get("er_beds_available"),
            "distance_miles": round(haversine_distance(
                req.latitude, req.longitude,
                h_data.get("latitude", 0), h_data.get("longitude", 0)
            ), 1) if h_data else None
        }})
    return enriched

# ─── Analytics ────────────────────────────────────────────────────────────────
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    hospitals = db.query(Hospital).all()
    total = len(hospitals)
    available = sum(1 for h in hospitals if h.status == "AVAILABLE")
    limited = sum(1 for h in hospitals if h.status == "LIMITED")
    full = sum(1 for h in hospitals if h.status == "FULL")
    avg_wait = sum(h.wait_time_minutes for h in hospitals) / total if total > 0 else 0
    total_er = sum(h.er_beds_total for h in hospitals)
    avail_er = sum(h.er_beds_available for h in hospitals)
    return {
        "total_hospitals": total,
        "status_breakdown": {"available": available, "limited": limited, "full": full},
        "avg_wait_minutes": round(avg_wait, 1),
        "total_er_beds": total_er,
        "available_er_beds": avail_er,
        "er_occupancy_pct": round((total_er - avail_er) / total_er * 100, 1) if total_er > 0 else 0,
        "trauma_centers": sum(1 for h in hospitals if h.is_trauma_center)
    }
