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


COMMISSION_RATE = 0.20
TAX_RATE = 0.11


def compute_splits(nightly, nights, cleaning_fee=150.0):
    gross = round(nightly * nights, 2)
    occupancy_tax = round(gross * TAX_RATE, 2)
    commission = round(gross * COMMISSION_RATE, 2)
    owner_payout = round(gross - occupancy_tax - commission, 2)
    return {
        "gross": gross, "cleaning_fee": round(cleaning_fee, 2),
        "occupancy_tax": occupancy_tax, "commission": commission,
        "maintenance_cost": 0.0, "owner_payout": owner_payout,
    }


IMG = {
    "ext1": "https://images.unsplash.com/photo-1596075610174-8431a5571cc3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
    "ext2": "https://images.unsplash.com/photo-1730005523015-422bd53dda0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
    "int1": "https://images.unsplash.com/photo-1779903726439-5c27e3996c8a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHw0fHxjb2FzdGFsJTIwaW50ZXJpb3IlMjBsaXZpbmclMjByb29tfGVufDB8fHx8MTc4MTkzMjMzMXww&ixlib=rb-4.1.0&q=85",
    "int2": "https://images.pexels.com/photos/14495875/pexels-photo-14495875.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    "maint": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODh8MHwxfHNlYXJjaHwyfHxtYWludGVuYW5jZSUyMHdvcmtlciUyMGh2YWN8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85",
}

GUEST_NAMES = [
    "Emily Carter", "Marcus Lee", "Priya Nair", "The Olsons", "James Whitfield",
    "Hannah Brooks", "Diego Santos", "Aisha Rahman", "Tom & Cara Nguyen",
    "Rebecca Stone", "The Patel Family", "Kyle Donovan", "Maya Fischer", "Grant Mosley",
]


async def seed_all(db):
    if await db.meta.find_one({"id": "seeded_v2"}):
        return

    for c in ["users", "properties", "maintenance", "housekeeping", "ledgers",
              "holds", "threads", "storm", "bookings", "guests", "meta"]:
        await db[c].delete_many({})

    now = datetime.utcnow()

    # ----- Users -----
    manager_id, hk_maria, hk_sofia = nid(), nid(), nid()
    mt_carlos, mt_diego = nid(), nid()
    owner_jim, owner_lin = nid(), nid()
    users = [
        {"id": manager_id, "email": "manager@coastline.com", "password_hash": hash_password("Manager123"), "name": "Dana Reyes", "role": "manager", "created_at": iso(now)},
        {"id": hk_maria, "email": "maria@coastline.com", "password_hash": hash_password("Field123"), "name": "Maria Gomez", "role": "housekeeper", "created_at": iso(now)},
        {"id": hk_sofia, "email": "sofia@coastline.com", "password_hash": hash_password("Field123"), "name": "Sofia Cruz", "role": "housekeeper", "created_at": iso(now)},
        {"id": mt_carlos, "email": "carlos@coastline.com", "password_hash": hash_password("Field123"), "name": "Carlos Mendez", "role": "maintenance", "created_at": iso(now)},
        {"id": mt_diego, "email": "diego@coastline.com", "password_hash": hash_password("Field123"), "name": "Diego Rivera", "role": "maintenance", "created_at": iso(now)},
        {"id": owner_jim, "email": "owner@coastline.com", "password_hash": hash_password("Owner123"), "name": "Jim Halloran", "role": "owner", "created_at": iso(now)},
        {"id": owner_lin, "email": "linda@coastline.com", "password_hash": hash_password("Owner123"), "name": "Linda Park", "role": "owner", "created_at": iso(now)},
    ]
    await db.users.insert_many(users)

    # ----- Properties (with rates) -----
    def prop(name, addr, owner_id, owner_name, beds, baths, coastal, img, nightly, occ):
        return {"id": nid(), "name": name, "address": addr, "owner_id": owner_id, "owner_name": owner_name,
                "beds": beds, "baths": baths, "coastal": coastal, "image": img, "nightly": nightly,
                "weekend_nightly": round(nightly * 1.25), "min_nights": 2, "cleaning_fee": 150, "occupancy": occ}
    props = [
        prop("Sandpiper Cottage", "112 Gulf Blvd, Destin, FL", owner_jim, "Jim Halloran", 3, 2, True, IMG["ext1"], 385, 78),
        prop("Pelican Perch", "8 Ocean Walk, Folly Beach, SC", owner_jim, "Jim Halloran", 4, 3, True, IMG["ext2"], 520, 71),
        prop("Salt & Pine Retreat", "44 Dune Dr, Gulf Shores, AL", owner_jim, "Jim Halloran", 2, 2, True, IMG["int2"], 295, 83),
        prop("Marsh View Villa", "30 Tidewater Ln, Hilton Head, SC", owner_lin, "Linda Park", 5, 4, True, IMG["int1"], 640, 69),
        prop("Coral Key Bungalow", "7 Sunset Cay, Naples, FL", owner_lin, "Linda Park", 3, 2, True, IMG["ext1"], 410, 75),
        prop("Magnolia Inland House", "210 Oak St, Mobile, AL", owner_lin, "Linda Park", 3, 2, False, IMG["int2"], 240, 64),
    ]
    await db.properties.insert_many(props)

    # ----- Guests -----
    guests = []
    for gname in GUEST_NAMES:
        guests.append({"id": nid(), "name": gname,
                       "email": gname.lower().replace(" ", ".").replace("&", "and").replace("..", ".") + "@email.com",
                       "phone": f"+1 (850) 555-{random.randint(1000,9999)}", "notes": "", "created_at": iso(now)})
    await db.guests.insert_many(guests)

    # ----- Bookings (past 4 months -> next 1 month) + derived ledgers + housekeeping -----
    bookings, ledgers, housekeeping = [], [], []
    channels = ["Airbnb", "VRBO", "Direct", "Booking.com"]
    for p in props:
        # walk a cursor day pointer through the window, place non-overlapping stays
        cursor = (now - timedelta(days=120)).date()
        end_window = (now + timedelta(days=30)).date()
        while cursor < end_window:
            gap = random.randint(1, 6)
            ci = cursor + timedelta(days=gap)
            nights = random.randint(2, 7)
            co = ci + timedelta(days=nights)
            if co > end_window:
                break
            nightly = p["nightly"] + random.choice([-20, 0, 0, 30])
            splits = compute_splits(nightly, nights, p["cleaning_fee"])
            guest = random.choice(guests)
            channel = random.choice(channels)
            ci_s, co_s, month = ci.isoformat(), co.isoformat(), ci.strftime("%Y-%m")
            status = "completed" if co < now.date() else "confirmed"
            bid = nid()
            bookings.append({"id": bid, "property_id": p["id"], "property_name": p["name"],
                             "owner_id": p["owner_id"], "guest_id": guest["id"], "guest_name": guest["name"],
                             "channel": channel, "check_in": ci_s, "check_out": co_s, "nights": nights,
                             "nightly": nightly, "status": status, "month": month, "created_at": iso(now), **splits})
            ledgers.append({"id": nid(), "booking_id": bid, "property_id": p["id"], "property_name": p["name"],
                            "owner_id": p["owner_id"], "month": month, "date": ci_s + "T00:00:00+00:00",
                            "channel": channel, "nights": nights, **splits})
            # housekeeping turnover for upcoming/near checkouts
            if co >= (now - timedelta(days=2)).date():
                st = "guest_ready" if co < now.date() else random.choice(["pending", "in_progress", "pending"])
                housekeeping.append({"id": nid(), "property_id": p["id"], "property_name": p["name"],
                                     "image": p["image"], "assigned_to": random.choice([hk_maria, hk_sofia, None]),
                                     "turnover_date": co_s + "T11:00:00+00:00", "status": st, "photos": [],
                                     "checkout_guest": guest["name"], "booking_id": bid, "created_at": iso(now)})
            cursor = co
    await db.bookings.insert_many(bookings)
    await db.ledgers.insert_many(ledgers)
    if housekeeping:
        await db.housekeeping.insert_many(housekeeping)

    # ----- Maintenance (predictive + active + one completed w/ photos) -----
    maint = []
    staff = [mt_carlos, mt_diego]
    for i, p in enumerate(props):
        if p["coastal"]:
            maint.append({"id": nid(), "property_id": p["id"], "property_name": p["name"],
                          "title": "Salt-corrosion check — HVAC condenser", "category": "salt_corrosion",
                          "priority": "normal", "status": "open", "assigned_to": staff[i % 2],
                          "notes": "Auto-scheduled every 60 days for coastal exposure.", "cost": 0.0,
                          "predictive": True, "storm": False, "before_photo": None, "after_photo": None,
                          "created_at": iso(now - timedelta(days=2)), "completed_at": None})
        maint.append({"id": nid(), "property_id": p["id"], "property_name": p["name"],
                      "title": "Replace HVAC filter (humidity strain)", "category": "hvac",
                      "priority": "normal", "status": "open" if i % 2 else "in_progress", "assigned_to": staff[i % 2],
                      "notes": "Auto-scheduled every 60 days.", "cost": 0.0,
                      "predictive": True, "storm": False, "before_photo": None, "after_photo": None,
                      "created_at": iso(now - timedelta(days=5)), "completed_at": None})
    maint.append({"id": nid(), "property_id": props[0]["id"], "property_name": props[0]["name"],
                  "title": "Repair corroded patio railing", "category": "salt_corrosion",
                  "priority": "high", "status": "completed", "assigned_to": mt_carlos,
                  "notes": "Salt corrosion replaced bolts & sealed railing.", "cost": 240.0,
                  "predictive": False, "storm": False, "before_photo": IMG["maint"], "after_photo": IMG["ext2"],
                  "created_at": iso(now - timedelta(days=12)), "completed_at": iso(now - timedelta(days=10))})
    await db.maintenance.insert_many(maint)

    # ----- Owner holds -----
    await db.holds.insert_one({"id": nid(), "property_id": props[0]["id"], "property_name": props[0]["name"],
                               "owner_id": owner_jim, "start_date": iso(now + timedelta(days=20)),
                               "end_date": iso(now + timedelta(days=27)), "note": "Family summer trip", "created_at": iso(now)})

    # ----- Inbox threads -----
    threads = [
        {"id": nid(), "guest": "Emily Carter", "property_name": props[0]["name"], "channel": "Airbnb",
         "preview": "Is the pool heated this time of year?", "unread": True, "last_at": iso(now - timedelta(hours=2)),
         "messages": [{"id": nid(), "from": "guest", "body": "Hi! We're booked next week. Is the pool heated this time of year?", "at": iso(now - timedelta(hours=2))}]},
        {"id": nid(), "guest": "Marcus Lee", "property_name": props[1]["name"], "channel": "VRBO",
         "preview": "How far is the beach access from the house?", "unread": True, "last_at": iso(now - timedelta(hours=5)),
         "messages": [{"id": nid(), "from": "guest", "body": "Looking forward to our stay. How far is the beach access from the house?", "at": iso(now - timedelta(hours=5))}]},
        {"id": nid(), "guest": "Priya Nair", "property_name": props[3]["name"], "channel": "SMS",
         "preview": "What's your hurricane cancellation policy?", "unread": False, "last_at": iso(now - timedelta(days=1)),
         "messages": [
             {"id": nid(), "from": "guest", "body": "We saw a storm in the forecast. What's your hurricane cancellation policy?", "at": iso(now - timedelta(days=1, hours=1))},
             {"id": nid(), "from": "host", "body": "Great question! If a mandatory evacuation is ordered, you'll receive a full refund for unused nights.", "at": iso(now - timedelta(days=1))}]},
        {"id": nid(), "guest": "The Olsons", "property_name": props[4]["name"], "channel": "Email",
         "preview": "Early check-in possible?", "unread": False, "last_at": iso(now - timedelta(days=2)),
         "messages": [{"id": nid(), "from": "guest", "body": "Any chance for an early check-in around noon?", "at": iso(now - timedelta(days=2))}]},
    ]
    await db.threads.insert_many(threads)

    await db.storm.insert_one({"id": "global", "active": False, "storm_name": None, "activated_at": None})
    await db.meta.insert_one({"id": "seeded_v2", "at": iso(now)})
