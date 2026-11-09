import asyncio, random
from datetime import datetime

async def simulate_capacity_changes(SessionLocal, Hospital, CapacityLog):
    """Background task: simulates real-time hospital capacity changes every 30 seconds."""
    while True:
        await asyncio.sleep(30)
        db = SessionLocal()
        try:
            hospitals = db.query(Hospital).all()
            for hospital in hospitals:
                # Simulate ±1-3 bed changes
                hospital.er_beds_available = max(0, min(
                    hospital.er_beds_total,
                    hospital.er_beds_available + random.randint(-3, 3)
                ))
                hospital.icu_beds_available = max(0, min(
                    hospital.icu_beds_total,
                    hospital.icu_beds_available + random.randint(-2, 2)
                ))
                # Update wait time
                hospital.wait_time_minutes = max(5, min(
                    180, hospital.wait_time_minutes + random.randint(-10, 10)
                ))
                # Recalculate status
                er_pct = hospital.er_beds_available / hospital.er_beds_total if hospital.er_beds_total > 0 else 0
                if er_pct > 0.3:
                    hospital.status = "AVAILABLE"
                elif er_pct > 0.1:
                    hospital.status = "LIMITED"
                else:
                    hospital.status = "FULL"
                hospital.last_updated = datetime.utcnow()
                db.add(CapacityLog(
                    hospital_id=hospital.id,
                    er_available=hospital.er_beds_available,
                    icu_available=hospital.icu_beds_available,
                    status=hospital.status
                ))
            db.commit()
        finally:
            db.close()
