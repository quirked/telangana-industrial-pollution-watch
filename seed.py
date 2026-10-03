from datetime import datetime, timezone
from html import escape
from pathlib import Path

from db import get_db


DEMO_REPORTS = (
    {
        "code": "INC-2026-0001", "title": "Red-tinted discharge near drainage channel",
        "observation": "Effluent / Wastewater Discharge", "industry": "Pharmaceuticals / Bulk Drugs / APIs",
        "description": "A red-tinted discharge was observed entering a roadside drainage channel near the industrial area.",
        "district": "Sangareddy", "locality": "Patancheru", "address": "Industrial Estate service road, near the drainage culvert",
        "unit": "Deccan BioChem Works — fictional", "date": "2026-10-01", "time": "16:20",
        "status": "Under Review", "remark": "Field inspection has been scheduled for preliminary review.",
        "action": "Regional inspection team notified.", "image": "demo-effluent.svg", "color": "#b33a3a",
    },
    {
        "code": "INC-2026-0002", "title": "Dense smoke visible above industrial stack",
        "observation": "Smoke / Air Emission", "industry": "Thermal Power",
        "description": "A dense grey smoke plume was visible from an industrial stack for an extended period.",
        "district": "Peddapalli", "locality": "Ramagundam", "address": "Northern industrial corridor, near service junction",
        "unit": "Telangana Energy Works — fictional", "date": "2026-09-30", "time": "09:40",
        "status": "Verified", "remark": "The submitted observation and location details have been reviewed.",
        "action": "A site verification visit has been recorded.", "image": "demo-smoke.svg", "color": "#4d6472",
    },
    {
        "code": "INC-2026-0003", "title": "Strong industrial fumes reported near estate road",
        "observation": "Fumes / Strong Industrial Odor", "industry": "Chemical Industry",
        "description": "Visible haze and a strong industrial odor were reported along the estate boundary road.",
        "district": "Medchal-Malkajgiri", "locality": "Jeedimetla", "address": "Phase II industrial estate boundary road",
        "unit": "MetroChem Industries — fictional", "date": "2026-10-02", "time": "18:05",
        "status": "Reported", "remark": None, "action": None, "image": "demo-fumes.svg", "color": "#796c91",
    },
    {
        "code": "INC-2026-0004", "title": "Heavy dust observed beside processing unit",
        "observation": "Dust / Particulate Emission", "industry": "Cement / Clinker",
        "description": "A sustained dust cloud was observed near material handling activity beside the main road.",
        "district": "Yadadri Bhuvanagiri", "locality": "Choutuppal", "address": "Industrial cluster approach road, east gate",
        "unit": "Eastern Clinker Works — fictional", "date": "2026-09-27", "time": "14:15",
        "status": "Resolved", "remark": "Review and follow-up action have been completed for this report.",
        "action": "Dust-control measures were reviewed and the case was closed.", "image": "demo-dust.svg", "color": "#a37742",
    },
)


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_demo_image(upload_dir, filename, color, title, locality):
    path = Path(upload_dir, filename)
    if path.exists():
        return
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#dce9e4"/><stop offset="1" stop-color="#f5eee0"/></linearGradient></defs>
<rect width="1200" height="720" fill="url(#sky)"/><rect y="510" width="1200" height="210" fill="#52625b"/>
<path d="M80 510V390h210v120M330 510V325h250v185M660 510V410h300v100" fill="#75827c"/>
<rect x="420" y="135" width="72" height="375" rx="6" fill="#58625f"/><path d="M456 150 C390 105 420 45 520 92 C590 20 720 68 690 155 C790 130 840 220 755 258 C630 288 520 220 456 150Z" fill="{escape(color)}" opacity=".82"/>
<rect x="48" y="42" width="650" height="116" rx="18" fill="#0b342c" opacity=".92"/><text x="82" y="91" fill="white" font-family="Arial" font-size="25" font-weight="700">DEMO EVIDENCE • REPORTED OBSERVATION</text><text x="82" y="130" fill="#d9f2e8" font-family="Arial" font-size="22">{escape(locality)}, Telangana</text>
<rect x="48" y="618" width="1104" height="62" rx="12" fill="#fff" opacity=".9"/><text x="76" y="658" fill="#183c34" font-family="Arial" font-size="23">{escape(title)}</text></svg>'''
    path.write_text(svg, encoding="utf-8")


def seed_database(upload_dir):
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] > 0:
        return False
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    now = utc_now()
    for demo in DEMO_REPORTS:
        _write_demo_image(upload_dir, demo["image"], demo["color"], demo["title"], demo["locality"])
        cursor = db.execute(
            """INSERT INTO reports
            (report_code, title, observation_type, industry_type, description, district, locality,
             address_landmark, industrial_unit_name, assigned_jurisdiction, incident_date,
             incident_time, image_filename, status, authority_remark, action_taken,
             submitter_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'demo-citizen', ?, ?)""",
            (demo["code"], demo["title"], demo["observation"], demo["industry"], demo["description"],
             demo["district"], demo["locality"], demo["address"], demo["unit"], demo["district"],
             demo["date"], demo["time"], demo["image"], demo["status"], demo["remark"],
             demo["action"], now, now),
        )
        report_id = cursor.lastrowid
        sequence = ["Reported"]
        if demo["status"] in ("Under Review", "Verified", "Action in Progress", "Resolved"):
            sequence.append("Under Review")
        if demo["status"] in ("Verified", "Action in Progress", "Resolved"):
            sequence.append("Verified")
        if demo["status"] in ("Action in Progress", "Resolved"):
            sequence.append("Action in Progress")
        if demo["status"] == "Resolved":
            sequence.append("Resolved")
        for index, status in enumerate(sequence):
            final = status == demo["status"]
            db.execute(
                "INSERT INTO status_history (report_id, status, public_remark, action_taken, actor, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (report_id, status, demo["remark"] if final else None, demo["action"] if final else None,
                 "Authority" if status != "Reported" else "Citizen", f"{demo['date']}T{10 + index:02d}:00:00+00:00"),
            )
    db.commit()
    return True
