import anthropic, json, os, math

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

AGENT_SYSTEM_PROMPT = """
You are an emergency medical triage routing agent for LA County.
Given a patient's symptoms/condition and their GPS location, plus a list of nearby hospitals
with real-time bed availability, recommend the TOP 3 best hospitals.

For each recommendation return a JSON array of objects with:
- hospital_id: integer
- hospital_name: string
- match_score: integer 1-100 (higher = better match)
- reason: one sentence why this hospital is best for this patient
- urgency: LOW / MEDIUM / HIGH / CRITICAL
- recommended_transport: DRIVE_YOURSELF / CALL_911

Prioritize: specialty match > availability > distance.
If symptoms suggest cardiac/stroke/trauma, always recommend CALL_911.
Return ONLY the JSON array, no markdown, no extra text.
"""

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_recommendation(symptoms: str, user_lat: float, user_lng: float, hospitals: list) -> list:
    # Add distance to each hospital
    for h in hospitals:
        h["distance_miles"] = round(haversine_distance(user_lat, user_lng, h["latitude"], h["longitude"]), 1)

    # Sort by distance, take nearest 15 to avoid token overload
    nearby = sorted(hospitals, key=lambda x: x["distance_miles"])[:15]

    hospital_context = "\n".join([
        f"ID:{h['id']} | {h['name']} | {h['city']} | "
        f"ER:{h['er_beds_available']}/{h['er_beds_total']} | "
        f"ICU:{h['icu_beds_available']}/{h['icu_beds_total']} | "
        f"Status:{h['status']} | Wait:{h['wait_time_minutes']}min | "
        f"Trauma:{h['is_trauma_center']} | Specialties:{h['specialties']} | "
        f"Distance:{h['distance_miles']}mi"
        for h in nearby
    ])

    prompt = f"Patient condition: {symptoms}\nPatient GPS: {user_lat}, {user_lng}\n\nNearby Hospitals:\n{hospital_context}\n\nRecommend top 3 hospitals."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=AGENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.content[0].text)
    except Exception as e:
        # Fallback: return 3 nearest available hospitals
        available = [h for h in nearby if h["status"] != "FULL"][:3]
        return [
            {"hospital_id": h["id"], "hospital_name": h["name"],
             "match_score": 70, "reason": "Nearest available hospital",
             "urgency": "MEDIUM", "recommended_transport": "DRIVE_YOURSELF"}
            for h in available
        ]
