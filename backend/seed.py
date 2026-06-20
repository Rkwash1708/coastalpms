import os
import uuid
import random
from datetime import datetime, timezone, timedelta

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def nid():
    return str(uuid.uuid4())


def iso(dt):
    return dt.replace(tzinfo=timezone.utc).isoformat()


IMG = {
    "ext1": "https://images.unsplash.com/photo-1596075610174-8431a5571cc3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
    "ext2": "https://images.unsplash.com/photo-1730005523015-422bd53dda0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
    "int1": "https://images.unsplash.com/photo-1779903726439-5c27e3996c8a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHw0fHxjb2FzdGFsJTIwaW50ZXJpb3IlMjBsaXZpbmclMjByb29tfGVufDB8fHx8MTc4MTkzMjMzMXww&ixlib=rb-4.1.0&q=85",
    "int2": "https://images.pexels.com/photos/14495875/pexels-photo-14495875.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    "maint": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODh8MHwxfHNlYXJjaHwyfHxtYWludGVuYW5jZSUyMHdvcmtlciUyMGh2YWN8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
    "hk": "https://images.pexels.com/photos/9462743/pexels-photo-9462743.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
}


async def seed_all(db):
    if await db.meta.find_one({"id": "seeded_v1"}):
        return

    await db.users.delete_many({})
    await db.properties.delete_many({})
    await db.maintenance.delete_many({})
    await db.housekeeping.delete_many({})
    await db.ledgers.delete_many({})
    await db.holds.delete_many({})
    await db.threads.delete_many({})
    await db.storm.delete_many({})

    # ----- Users -----
    manager_id = nid()
    hk_maria = nid()
    hk_sofia = nid()
    mt_carlos = nid()
    mt_diego = nid()
    owner_jim = nid()
    owner_lin = nid()

    users = [
        {"id": manager_id, "email": "manager@coastline.com", "password_hash": hash_password("Manager123"), "name": "Dana Reyes", "role": "manager", "created_at": iso(datetime.utcnow())},
        {"id": hk_maria, "email": "maria@coastline.com", "password_hash": hash_password("Field123"), "name": "Maria Gomez", "role": "housekeeper", "created_at": iso(datetime.utcnow())},
        {"id": hk_sofia, "email": "sofia@coastline.com", "password_hash": hash_password("Field123"), "name": "Sofia Cruz", "role": "housekeeper", "created_at": iso(datetime.utcnow())},
        {"id": mt_carlos, "email": "carlos@coastline.com", "password_hash": hash_password("Field123"), "name": "Carlos Mendez", "role": "maintenance", "created_at": iso(datetime.utcnow())},
        {"id": mt_diego, "email": "diego@coastline.com", "password_hash": hash_password("Field123"), "name": "Diego Rivera", "role": "maintenance", "created_at": iso(datetime.utcnow())},
        {"id": owner_jim, "email": "owner@coastline.com", "password_hash": hash_password("Owner123"), "name": "Jim Halloran", "role": "owner", "created_at": iso(datetime.utcnow())},
        {"id": owner_lin, "email": "linda@coastline.com", "password_hash": hash_password("Owner123"), "name": "Linda Park", "role": "owner", "created_at": iso(datetime.utcnow())},
    ]
    await db.users.insert_many(users)

    # ----- Properties -----
    props = [
        {"id": nid(), "name": "Sandpiper Cottage", "address": "112 Gulf Blvd, Destin, FL", "owner_id": owner_jim, "owner_name": "Jim Halloran", "beds": 3, "baths": 2, "coastal": True, "image": IMG["ext1"], "nightly": 385, "occupancy": 78},
        {"id": nid(), "name": "Pelican Perch", "address": "8 Ocean Walk, Folly Beach, SC", "owner_id": owner_jim, "owner_name": "Jim Halloran", "beds": 4, "baths": 3, "coastal": True, "image": IMG["ext2"], "nightly": 520, "occupancy": 71},
        {"id": nid(), "name": "Salt & Pine Retreat", "address": "44 Dune Dr, Gulf Shores, AL", "owner_id": owner_jim, "owner_name": "Jim Halloran", "beds": 2, "baths": 2, "coastal": True, "image": IMG["int2"], "nightly": 295, "occupancy": 83},
        {"id": nid(), "name": "Marsh View Villa", "address": "30 Tidewater Ln, Hilton Head, SC", "owner_id": owner_lin, "owner_name": "Linda Park", "beds": 5, "baths": 4, "coastal": True, "image": IMG["int1"], "nightly": 640, "occupancy": 69},
        {"id": nid(), "name": "Coral Key Bungalow", "address": "7 Sunset Cay, Naples, FL", "owner_id": owner_lin, "owner_name": "Linda Park", "beds": 3, "baths": 2, "coastal": True, "image": IMG["ext1"], "nightly": 410, "occupancy": 75},
        {"id": nid(), "name": "Magnolia Inland House", "address": "210 Oak St, Mobile, AL", "owner_id": owner_lin, "owner_name": "Linda Park", "beds": 3, "baths": 2, "coastal": False, "image": IMG["int2"], "nightly": 240, "occupancy": 64},
    ]
    await db.properties.insert_many(props)

    # ----- Maintenance (predictive + active) -----
    now = datetime.utcnow()
    maint = []
    staff = [mt_carlos, mt_diego]
    for i, p in enumerate(props):
        if p["coastal"]:
            maint.append({
                "id": nid(), "property_id": p["id"], "property_name": p["name"],
                "title": "Salt-corrosion check — HVAC condenser", "category": "salt_corrosion",
                "priority": "normal", "status": "open", "assigned_to": staff[i % 2],
                "notes": "Auto-scheduled every 60 days for coastal exposure.", "cost": 0.0,
                "predictive": True, "storm": False, "before_photo": None, "after_photo": None,
                "created_at": iso(now - timedelta(days=2)), "completed_at": None,
            })
        maint.append({
            "id": nid(), "property_id": p["id"], "property_name": p["name"],
            "title": "Replace HVAC filter (humidity strain)", "category": "hvac",
            "priority": "normal", "status": "open" if i % 2 else "in_progress", "assigned_to": staff[i % 2],
            "notes": "Auto-scheduled every 60 days.", "cost": 0.0,
            "predictive": True, "storm": False, "before_photo": None, "after_photo": None,
            "created_at": iso(now - timedelta(days=5)), "completed_at": None,
        })
    # a completed one with before/after + cost (feeds owner portal)
    maint.append({
        "id": nid(), "property_id": props[0]["id"], "property_name": props[0]["name"],
        "title": "Repair corroded patio railing", "category": "salt_corrosion",
        "priority": "high", "status": "completed", "assigned_to": mt_carlos,
        "notes": "Salt corrosion replaced bolts & sealed railing.", "cost": 240.0,
        "predictive": False, "storm": False,
        "before_photo": IMG["maint"], "after_photo": IMG["ext2"],
        "created_at": iso(now - timedelta(days=12)), "completed_at": iso(now - timedelta(days=10)),
    })
    await db.maintenance.insert_many(maint)

    # ----- Housekeeping -----
    hk = []
    hks = [hk_maria, hk_sofia]
    statuses = ["pending", "in_progress", "guest_ready", "pending"]
    for i, p in enumerate(props):
        hk.append({
            "id": nid(), "property_id": p["id"], "property_name": p["name"],
            "image": p["image"], "assigned_to": hks[i % 2],
            "turnover_date": iso(now + timedelta(days=i % 3)),
            "status": statuses[i % len(statuses)], "photos": [],
            "checkout_guest": "Guest party of 4", "created_at": iso(now),
        })
    await db.housekeeping.insert_many(hk)

    # ----- Ledgers (split accounting, 6 months) -----
    ledgers = []
    months = []
    for m in range(5, -1, -1):
        d = now.replace(day=1) - timedelta(days=30 * m)
        months.append(d.strftime("%Y-%m"))
    for p in props:
        for mi, month in enumerate(months):
            n_bookings = random.randint(2, 4)
            for b in range(n_bookings):
                nights = random.randint(3, 7)
                gross = round(p["nightly"] * nights, 2)
                cleaning = round(135 + random.randint(0, 40), 2)
                tax = round(gross * 0.11, 2)  # 11% occupancy tax
                commission = round(gross * 0.20, 2)  # 20% PMC commission
                maint_cost = round(random.choice([0, 0, 0, 60, 240]), 2)
                owner_payout = round(gross - commission - tax - maint_cost, 2)
                ledgers.append({
                    "id": nid(), "property_id": p["id"], "property_name": p["name"],
                    "owner_id": p["owner_id"], "month": month,
                    "date": iso(datetime.strptime(month, "%Y-%m") + timedelta(days=random.randint(1, 26))),
                    "channel": random.choice(["Airbnb", "VRBO", "Direct"]),
                    "nights": nights, "gross": gross, "cleaning_fee": cleaning,
                    "occupancy_tax": tax, "commission": commission,
                    "maintenance_cost": maint_cost, "owner_payout": owner_payout,
                })
    await db.ledgers.insert_many(ledgers)

    # ----- Owner holds -----
    holds = [{
        "id": nid(), "property_id": props[0]["id"], "property_name": props[0]["name"],
        "owner_id": owner_jim, "start_date": iso(now + timedelta(days=20)),
        "end_date": iso(now + timedelta(days=27)), "note": "Family summer trip",
        "created_at": iso(now),
    }]
    await db.holds.insert_many(holds)

    # ----- Inbox threads -----
    threads = [
        {"id": nid(), "guest": "Emily Carter", "property_name": props[0]["name"], "channel": "Airbnb",
         "preview": "Is the pool heated this time of year?", "unread": True, "last_at": iso(now - timedelta(hours=2)),
         "messages": [
             {"id": nid(), "from": "guest", "body": "Hi! We're booked next week. Is the pool heated this time of year?", "at": iso(now - timedelta(hours=2))},
         ]},
        {"id": nid(), "guest": "Marcus Lee", "property_name": props[1]["name"], "channel": "VRBO",
         "preview": "How far is the beach access from the house?", "unread": True, "last_at": iso(now - timedelta(hours=5)),
         "messages": [
             {"id": nid(), "from": "guest", "body": "Looking forward to our stay. How far is the beach access from the house?", "at": iso(now - timedelta(hours=5))},
         ]},
        {"id": nid(), "guest": "Priya N.", "property_name": props[3]["name"], "channel": "SMS",
         "preview": "What's your hurricane cancellation policy?", "unread": False, "last_at": iso(now - timedelta(days=1)),
         "messages": [
             {"id": nid(), "from": "guest", "body": "We saw a storm in the forecast. What's your hurricane cancellation policy?", "at": iso(now - timedelta(days=1, hours=1))},
             {"id": nid(), "from": "host", "body": "Great question! If a mandatory evacuation is ordered, you'll receive a full refund for unused nights.", "at": iso(now - timedelta(days=1))},
         ]},
        {"id": nid(), "guest": "The Olsons", "property_name": props[4]["name"], "channel": "Email",
         "preview": "Early check-in possible?", "unread": False, "last_at": iso(now - timedelta(days=2)),
         "messages": [
             {"id": nid(), "from": "guest", "body": "Any chance for an early check-in around noon?", "at": iso(now - timedelta(days=2))},
         ]},
    ]
    await db.threads.insert_many(threads)

    await db.storm.insert_one({"id": "global", "active": False, "storm_name": None, "activated_at": None})
    await db.meta.insert_one({"id": "seeded_v1", "at": iso(datetime.utcnow())})
