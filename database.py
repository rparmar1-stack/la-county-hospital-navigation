from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Hospital, Admin
import json, os, random
from passlib.context import CryptContext
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./la_hospitals.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def random_avail(total, min_pct=0.1, max_pct=0.9):
    return random.randint(int(total * min_pct), int(total * max_pct))

def compute_status(er_total, er_avail):
    pct = er_avail / er_total if er_total > 0 else 0
    if pct > 0.3: return "AVAILABLE"
    if pct > 0.1: return "LIMITED"
    return "FULL"

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Hospital).count() == 0:
            seed_hospitals(db)
        if db.query(Admin).count() == 0:
            db.add(Admin(username="admin",
                         hashed_password=pwd_context.hash("admin123"),
                         hospital_id=1))
            db.commit()
    finally:
        db.close()

def seed_hospitals(db):
    hospitals_data = [
        {"name": "Cedars-Sinai Medical Center", "address": "8700 Beverly Blvd",
         "city": "Los Angeles", "latitude": 34.0762, "longitude": -118.3803,
         "phone": "(310) 423-3277", "er_beds_total": 80, "icu_beds_total": 60,
         "general_beds_total": 400, "pediatric_beds_total": 40,
         "is_trauma_center": True,
         "specialties": json.dumps(["Cardiac", "Neurology", "Oncology", "Trauma", "Stroke Center"])},
        {"name": "UCLA Ronald Reagan Medical Center", "address": "757 Westwood Plaza",
         "city": "Los Angeles", "latitude": 34.0663, "longitude": -118.4452,
         "phone": "(310) 825-9111", "er_beds_total": 70, "icu_beds_total": 55,
         "general_beds_total": 350, "pediatric_beds_total": 50,
         "is_trauma_center": True,
         "specialties": json.dumps(["Cardiac", "Neurology", "Transplant", "Trauma", "Burn Center"])},
        {"name": "Keck Hospital of USC", "address": "1500 San Pablo St",
         "city": "Los Angeles", "latitude": 34.0617, "longitude": -118.2009,
         "phone": "(323) 442-8500", "er_beds_total": 60, "icu_beds_total": 45,
         "general_beds_total": 300, "pediatric_beds_total": 30,
         "is_trauma_center": True,
         "specialties": json.dumps(["Cardiac", "Transplant", "Oncology", "Trauma"])},
        {"name": "LAC+USC Medical Center", "address": "2051 Marengo St",
         "city": "Los Angeles", "latitude": 34.0572, "longitude": -118.1987,
         "phone": "(323) 409-1000", "er_beds_total": 100, "icu_beds_total": 80,
         "general_beds_total": 600, "pediatric_beds_total": 60,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Burn Center", "Neurology", "Cardiac"])},
        {"name": "Cedars-Sinai Marina del Rey Hospital", "address": "4650 Lincoln Blvd",
         "city": "Marina del Rey", "latitude": 33.9802, "longitude": -118.4431,
         "phone": "(310) 823-8911", "er_beds_total": 40, "icu_beds_total": 20,
         "general_beds_total": 145, "pediatric_beds_total": 10,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Orthopedics", "General Surgery"])},
        {"name": "Providence Saint John's Health Center", "address": "2121 Santa Monica Blvd",
         "city": "Santa Monica", "latitude": 34.0244, "longitude": -118.4731,
         "phone": "(310) 829-5511", "er_beds_total": 45, "icu_beds_total": 25,
         "general_beds_total": 200, "pediatric_beds_total": 15,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Cancer", "Neurology", "Orthopedics"])},
        {"name": "Ronald Reagan UCLA Medical Center - Santa Monica", "address": "1250 16th St",
         "city": "Santa Monica", "latitude": 34.0339, "longitude": -118.4912,
         "phone": "(310) 319-4000", "er_beds_total": 35, "icu_beds_total": 20,
         "general_beds_total": 265, "pediatric_beds_total": 0,
         "is_trauma_center": False,
         "specialties": json.dumps(["Orthopedics", "Oncology", "General Surgery"])},
        {"name": "Children's Hospital Los Angeles", "address": "4650 Sunset Blvd",
         "city": "Los Angeles", "latitude": 34.0965, "longitude": -118.2900,
         "phone": "(323) 660-2450", "er_beds_total": 50, "icu_beds_total": 40,
         "general_beds_total": 350, "pediatric_beds_total": 300,
         "is_trauma_center": True,
         "specialties": json.dumps(["Pediatric", "Pediatric Oncology", "Pediatric Cardiac", "Neonatal"])},
        {"name": "Huntington Hospital", "address": "100 W California Blvd",
         "city": "Pasadena", "latitude": 34.1425, "longitude": -118.1444,
         "phone": "(626) 397-5000", "er_beds_total": 55, "icu_beds_total": 35,
         "general_beds_total": 280, "pediatric_beds_total": 25,
         "is_trauma_center": True,
         "specialties": json.dumps(["Cardiac", "Neurology", "Trauma", "Cancer"])},
        {"name": "Methodist Hospital of Southern California", "address": "300 W Huntington Dr",
         "city": "Arcadia", "latitude": 34.1397, "longitude": -118.0364,
         "phone": "(626) 898-8000", "er_beds_total": 40, "icu_beds_total": 22,
         "general_beds_total": 200, "pediatric_beds_total": 15,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Orthopedics", "Neurology"])},
        {"name": "Kaiser Permanente Los Angeles Medical Center", "address": "4867 Sunset Blvd",
         "city": "Los Angeles", "latitude": 34.0978, "longitude": -118.2955,
         "phone": "(323) 783-4011", "er_beds_total": 65, "icu_beds_total": 40,
         "general_beds_total": 320, "pediatric_beds_total": 30,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Cancer", "Orthopedics", "Neurology"])},
        {"name": "Good Samaritan Hospital", "address": "1225 Wilshire Blvd",
         "city": "Los Angeles", "latitude": 34.0572, "longitude": -118.2687,
         "phone": "(213) 977-2121", "er_beds_total": 45, "icu_beds_total": 28,
         "general_beds_total": 220, "pediatric_beds_total": 20,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Neurology", "Orthopedics"])},
        {"name": "Hollywood Presbyterian Medical Center", "address": "1300 N Vermont Ave",
         "city": "Los Angeles", "latitude": 34.0942, "longitude": -118.2917,
         "phone": "(213) 413-3000", "er_beds_total": 50, "icu_beds_total": 30,
         "general_beds_total": 200, "pediatric_beds_total": 18,
         "is_trauma_center": False,
         "specialties": json.dumps(["General Surgery", "Orthopedics", "Cardiac"])},
        {"name": "Dignity Health - California Hospital Medical Center", "address": "1401 S Grand Ave",
         "city": "Los Angeles", "latitude": 34.0391, "longitude": -118.2650,
         "phone": "(213) 748-2411", "er_beds_total": 55, "icu_beds_total": 32,
         "general_beds_total": 250, "pediatric_beds_total": 22,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Cardiac", "Neurology", "General Surgery"])},
        {"name": "Torrance Memorial Medical Center", "address": "3330 Lomita Blvd",
         "city": "Torrance", "latitude": 33.8015, "longitude": -118.3468,
         "phone": "(310) 325-9110", "er_beds_total": 55, "icu_beds_total": 35,
         "general_beds_total": 300, "pediatric_beds_total": 25,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Cancer", "Orthopedics", "Neurology"])},
        {"name": "Harbor-UCLA Medical Center", "address": "1000 W Carson St",
         "city": "Torrance", "latitude": 33.8654, "longitude": -118.3098,
         "phone": "(310) 222-2345", "er_beds_total": 75, "icu_beds_total": 50,
         "general_beds_total": 400, "pediatric_beds_total": 40,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Burn Center", "Neurology", "Cardiac"])},
        {"name": "Providence Little Company of Mary Medical Center", "address": "4101 Torrance Blvd",
         "city": "Torrance", "latitude": 33.8329, "longitude": -118.3505,
         "phone": "(310) 540-7676", "er_beds_total": 42, "icu_beds_total": 22,
         "general_beds_total": 180, "pediatric_beds_total": 12,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Oncology", "Orthopedics"])},
        {"name": "Adventist Health White Memorial", "address": "1720 Cesar E Chavez Ave",
         "city": "Los Angeles", "latitude": 34.0525, "longitude": -118.2103,
         "phone": "(323) 268-5000", "er_beds_total": 48, "icu_beds_total": 28,
         "general_beds_total": 220, "pediatric_beds_total": 20,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Cardiac", "Neurology", "Neonatal"])},
        {"name": "Pomona Valley Hospital Medical Center", "address": "1798 N Garey Ave",
         "city": "Pomona", "latitude": 34.0786, "longitude": -117.7378,
         "phone": "(909) 865-9500", "er_beds_total": 60, "icu_beds_total": 38,
         "general_beds_total": 280, "pediatric_beds_total": 25,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Cardiac", "Cancer", "Orthopedics"])},
        {"name": "Northridge Hospital Medical Center", "address": "18300 Roscoe Blvd",
         "city": "Northridge", "latitude": 34.2284, "longitude": -118.5356,
         "phone": "(818) 885-8500", "er_beds_total": 52, "icu_beds_total": 30,
         "general_beds_total": 240, "pediatric_beds_total": 18,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Neurology", "Orthopedics", "Cancer"])},
        {"name": "Providence Cedars-Sinai Tarzana Medical Center", "address": "18321 Clark St",
         "city": "Tarzana", "latitude": 34.1717, "longitude": -118.5490,
         "phone": "(818) 881-0800", "er_beds_total": 45, "icu_beds_total": 25,
         "general_beds_total": 200, "pediatric_beds_total": 15,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Orthopedics", "Cancer"])},
        {"name": "Henry Mayo Newhall Hospital", "address": "23845 McBean Pkwy",
         "city": "Valencia", "latitude": 34.4072, "longitude": -118.5631,
         "phone": "(661) 253-8000", "er_beds_total": 38, "icu_beds_total": 20,
         "general_beds_total": 180, "pediatric_beds_total": 12,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "General Surgery", "Orthopedics"])},
        {"name": "PIH Health Whittier Hospital", "address": "12401 Washington Blvd",
         "city": "Whittier", "latitude": 33.9798, "longitude": -118.0282,
         "phone": "(562) 698-0811", "er_beds_total": 45, "icu_beds_total": 24,
         "general_beds_total": 200, "pediatric_beds_total": 16,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Cancer", "Orthopedics"])},
        {"name": "Centinela Hospital Medical Center", "address": "555 E Hardy St",
         "city": "Inglewood", "latitude": 33.9572, "longitude": -118.3531,
         "phone": "(310) 673-4660", "er_beds_total": 42, "icu_beds_total": 22,
         "general_beds_total": 175, "pediatric_beds_total": 10,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Orthopedics", "General Surgery"])},
        {"name": "MLK Community Hospital", "address": "1680 E 120th St",
         "city": "Los Angeles", "latitude": 33.9316, "longitude": -118.2479,
         "phone": "(424) 338-8000", "er_beds_total": 50, "icu_beds_total": 28,
         "general_beds_total": 131, "pediatric_beds_total": 10,
         "is_trauma_center": False,
         "specialties": json.dumps(["General Surgery", "Cardiac", "Obstetrics"])},
        {"name": "Glendale Memorial Hospital", "address": "1420 S Central Ave",
         "city": "Glendale", "latitude": 34.1286, "longitude": -118.2554,
         "phone": "(818) 502-1900", "er_beds_total": 48, "icu_beds_total": 26,
         "general_beds_total": 220, "pediatric_beds_total": 15,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Stroke Center", "Orthopedics"])},
        {"name": "Adventist Health Glendale", "address": "1509 Wilson Terrace",
         "city": "Glendale", "latitude": 34.1514, "longitude": -118.2607,
         "phone": "(818) 409-8000", "er_beds_total": 52, "icu_beds_total": 30,
         "general_beds_total": 250, "pediatric_beds_total": 20,
         "is_trauma_center": True,
         "specialties": json.dumps(["Cardiac", "Cancer", "Neurology", "Trauma"])},
        {"name": "Emanate Health - Inter-Community Hospital", "address": "210 W San Bernardino Rd",
         "city": "Covina", "latitude": 34.0866, "longitude": -117.8815,
         "phone": "(626) 331-7331", "er_beds_total": 40, "icu_beds_total": 20,
         "general_beds_total": 180, "pediatric_beds_total": 12,
         "is_trauma_center": False,
         "specialties": json.dumps(["Cardiac", "Orthopedics", "General Surgery"])},
        {"name": "Sutter Health CPMC - Mission Bernal Campus", "address": "3555 Cesar Chavez St",
         "city": "Los Angeles", "latitude": 34.0206, "longitude": -118.2437,
         "phone": "(323) 560-4000", "er_beds_total": 38, "icu_beds_total": 18,
         "general_beds_total": 160, "pediatric_beds_total": 10,
         "is_trauma_center": False,
         "specialties": json.dumps(["General Surgery", "Cardiac", "Orthopedics"])},
        {"name": "St. Francis Medical Center", "address": "3630 E Imperial Hwy",
         "city": "Lynwood", "latitude": 33.9295, "longitude": -118.1956,
         "phone": "(310) 900-8900", "er_beds_total": 45, "icu_beds_total": 24,
         "general_beds_total": 200, "pediatric_beds_total": 15,
         "is_trauma_center": True,
         "specialties": json.dumps(["Trauma", "Cardiac", "Neurology", "Neonatal"])},
    ]

    for h in hospitals_data:
        er_total = h["er_beds_total"]
        icu_total = h["icu_beds_total"]
        gen_total = h["general_beds_total"]
        ped_total = h["pediatric_beds_total"]
        er_avail = random_avail(er_total)
        icu_avail = random_avail(icu_total)
        status = compute_status(er_total, er_avail)
        wait = random.randint(15, 120)

        hospital = Hospital(
            name=h["name"], address=h["address"], city=h["city"],
            latitude=h["latitude"], longitude=h["longitude"], phone=h["phone"],
            er_beds_total=er_total, er_beds_available=er_avail,
            icu_beds_total=icu_total, icu_beds_available=icu_avail,
            general_beds_total=gen_total, general_beds_available=random_avail(gen_total),
            pediatric_beds_total=ped_total, pediatric_beds_available=random_avail(ped_total) if ped_total > 0 else 0,
            specialties=h["specialties"], status=status,
            wait_time_minutes=wait, is_trauma_center=h["is_trauma_center"],
            last_updated=datetime.utcnow()
        )
        db.add(hospital)
    db.commit()
