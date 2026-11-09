from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    address = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String, default="(213) 555-0100")
    er_beds_total = Column(Integer, default=50)
    er_beds_available = Column(Integer, default=25)
    icu_beds_total = Column(Integer, default=30)
    icu_beds_available = Column(Integer, default=15)
    general_beds_total = Column(Integer, default=200)
    general_beds_available = Column(Integer, default=100)
    pediatric_beds_total = Column(Integer, default=20)
    pediatric_beds_available = Column(Integer, default=10)
    specialties = Column(Text, default='[]')
    status = Column(String, default="AVAILABLE")
    wait_time_minutes = Column(Integer, default=30)
    is_trauma_center = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    logs = relationship("CapacityLog", back_populates="hospital")

class CapacityLog(Base):
    __tablename__ = "capacity_logs"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    er_available = Column(Integer)
    icu_available = Column(Integer)
    status = Column(String)
    logged_at = Column(DateTime, default=datetime.utcnow)
    hospital = relationship("Hospital", back_populates="logs")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
