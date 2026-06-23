from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import bcrypt
import jwt
from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr

from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutStatusResponse,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']
STRIPE_API_KEY = os.environ['STRIPE_API_KEY']

app = FastAPI(title="Coastline PMS")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coastline")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_roles(*roles):
    async def checker(user: dict = Depends(get_current_user)):
        if roles and user["role"] not in roles and user["role"] != "manager":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "owner"


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class PhotoPair(BaseModel):
    before: Optional[str] = None
    after: Optional[str] = None


class MaintenanceCreate(BaseModel):
    property_id: str
    title: str
    category: str = "general"  # hvac, salt_corrosion, plumbing, storm_prep, general
    priority: str = "normal"   # normal, high, urgent
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    cost: float = 0.0


class TaskStatusUpdate(BaseModel):
    status: str


class GuestReadyInput(BaseModel):
    photo: str  # base64 data url


class MaintenancePhotoInput(BaseModel):
    before: Optional[str] = None
    after: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class OwnerHoldCreate(BaseModel):
    property_id: str
    start_date: str
    end_date: str
    note: Optional[str] = None


class MessageInput(BaseModel):
    body: str


class AIReplyInput(BaseModel):
    thread_id: str


class TranslateInput(BaseModel):
    text: str
    target: str = "es"


class BookingCreate(BaseModel):
    property_id: str
    guest_name: str
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    check_in: str   # YYYY-MM-DD
    check_out: str  # YYYY-MM-DD
    channel: str = "Direct"
    nightly: Optional[float] = None


class BookingStatusUpdate(BaseModel):
    status: str


class RatesUpdate(BaseModel):
    nightly: Optional[float] = None
    weekend_nightly: Optional[float] = None
    min_nights: Optional[int] = None
    cleaning_fee: Optional[float] = None


class CheckoutInput(BaseModel):
    property_id: str
    guest_name: str
    guest_email: str
    check_in: str
    check_out: str
    origin_url: str


COMMISSION_RATE = 0.20
TAX_RATE = 0.11


def compute_splits(nightly: float, nights: int, cleaning_fee: float = 150.0):
    gross = round(nightly * nights, 2)
    occupancy_tax = round(gross * TAX_RATE, 2)
    commission = round(gross * COMMISSION_RATE, 2)
    owner_payout = round(gross - occupancy_tax - commission, 2)
    return {
        "gross": gross,
        "cleaning_fee": round(cleaning_fee, 2),
        "occupancy_tax": occupancy_tax,
        "commission": commission,
        "maintenance_cost": 0.0,
        "owner_payout": owner_payout,
    }


def nights_between(check_in: str, check_out: str) -> int:
    d1 = datetime.fromisoformat(check_in)
    d2 = datetime.fromisoformat(check_out)
    return max(1, (d2 - d1).days)


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api.post("/auth/register")
async def register(inp: RegisterInput):
    email = inp.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = new_id()
    doc = {
        "id": uid,
        "email": email,
        "password_hash": hash_password(inp.password),
        "name": inp.name,
        "role": inp.role,
        "created_at": now_iso(),
    }
    await db.users.insert_one(doc)
    token = create_access_token(uid, email, inp.role)
    return {"token": token, "user": {"id": uid, "email": email, "name": inp.name, "role": inp.role}}


@api.post("/auth/login")
async def login(inp: LoginInput):
    email = inp.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(inp.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email, user["role"])
    return {
        "token": token,
        "user": {"id": user["id"], "email": email, "name": user["name"], "role": user["role"]},
    }


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@api.get("/team")
async def team(user: dict = Depends(get_current_user)):
    members = await db.users.find(
        {"role": {"$in": ["housekeeper", "maintenance", "manager"]}}, {"_id": 0, "password_hash": 0}
    ).to_list(100)
    return members


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
@api.get("/properties")
async def list_properties(user: dict = Depends(get_current_user)):
    q = {}
    if user["role"] == "owner":
        q = {"owner_id": user["id"]}
    props = await db.properties.find(q, {"_id": 0}).to_list(200)
    return props


@api.get("/properties/{pid}")
async def get_property(pid: str, user: dict = Depends(get_current_user)):
    prop = await db.properties.find_one({"id": pid}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


# ---------------------------------------------------------------------------
# Maintenance tasks
# ---------------------------------------------------------------------------
@api.get("/maintenance")
async def list_maintenance(user: dict = Depends(get_current_user)):
    q = {}
    if user["role"] == "owner":
        owned = await db.properties.find({"owner_id": user["id"]}, {"id": 1, "_id": 0}).to_list(200)
        q = {"property_id": {"$in": [p["id"] for p in owned]}}
    elif user["role"] == "maintenance":
        q = {"$or": [{"assigned_to": user["id"]}, {"assigned_to": None}]}
    tasks = await db.maintenance.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    return tasks


@api.post("/maintenance")
async def create_maintenance(inp: MaintenanceCreate, user: dict = Depends(require_roles("manager", "maintenance"))):
    prop = await db.properties.find_one({"id": inp.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    doc = {
        "id": new_id(),
        "property_id": inp.property_id,
        "property_name": prop["name"],
        "title": inp.title,
        "category": inp.category,
        "priority": inp.priority,
        "status": "open",
        "assigned_to": inp.assigned_to,
        "notes": inp.notes,
        "cost": inp.cost,
        "predictive": False,
        "storm": inp.category == "storm_prep",
        "before_photo": None,
        "after_photo": None,
        "created_at": now_iso(),
        "completed_at": None,
    }
    await db.maintenance.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.patch("/maintenance/{tid}")
async def update_maintenance(tid: str, inp: MaintenancePhotoInput, user: dict = Depends(get_current_user)):
    task = await db.maintenance.find_one({"id": tid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = {}
    if inp.before is not None:
        updates["before_photo"] = inp.before
    if inp.after is not None:
        updates["after_photo"] = inp.after
    if inp.cost is not None:
        updates["cost"] = inp.cost
    if inp.notes is not None:
        updates["notes"] = inp.notes
    if inp.status is not None:
        updates["status"] = inp.status
        if inp.status == "completed":
            updates["completed_at"] = now_iso()
    await db.maintenance.update_one({"id": tid}, {"$set": updates})
    updated = await db.maintenance.find_one({"id": tid}, {"_id": 0})
    return updated


# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------
@api.get("/housekeeping")
async def list_housekeeping(user: dict = Depends(get_current_user)):
    q = {}
    if user["role"] == "housekeeper":
        q = {"$or": [{"assigned_to": user["id"]}, {"assigned_to": None}]}
    tasks = await db.housekeeping.find(q, {"_id": 0}).sort("turnover_date", 1).to_list(500)
    return tasks


@api.post("/housekeeping/{tid}/guest-ready")
async def mark_guest_ready(tid: str, inp: GuestReadyInput, user: dict = Depends(get_current_user)):
    task = await db.housekeeping.find_one({"id": tid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    photos = task.get("photos", [])
    photos.append({"url": inp.photo, "timestamp": now_iso(), "by": user["name"]})
    await db.housekeeping.update_one(
        {"id": tid},
        {"$set": {"status": "guest_ready", "photos": photos, "completed_at": now_iso()}},
    )
    return await db.housekeeping.find_one({"id": tid}, {"_id": 0})


# ---------------------------------------------------------------------------
# Storm mode
# ---------------------------------------------------------------------------
STORM_CHECKLIST = [
    "Secure all patio furniture & umbrellas",
    "Install / verify storm shutters",
    "Photograph property condition (insurance)",
    "Shut off main water valve",
    "Clear gutters & drains",
    "Bring in grills and loose decor",
    "Verify generator fuel level",
    "Confirm guest evacuation / check-out status",
]


@api.get("/storm/status")
async def storm_status(user: dict = Depends(get_current_user)):
    s = await db.storm.find_one({"id": "global"}, {"_id": 0})
    if not s:
        s = {"id": "global", "active": False, "storm_name": None, "activated_at": None}
    return s


@api.post("/storm/activate")
async def storm_activate(payload: dict, user: dict = Depends(require_roles("manager"))):
    storm_name = payload.get("storm_name", "Tropical Storm")
    active = payload.get("active", True)
    await db.storm.update_one(
        {"id": "global"},
        {"$set": {"id": "global", "active": active, "storm_name": storm_name if active else None,
                  "activated_at": now_iso() if active else None}},
        upsert=True,
    )
    if active:
        props = await db.properties.find({}, {"_id": 0}).to_list(200)
        staff = await db.users.find({"role": {"$in": ["housekeeper", "maintenance"]}}).to_list(50)
        staff_ids = [s["id"] for s in staff]
        for i, prop in enumerate(props):
            existing = await db.maintenance.find_one({"property_id": prop["id"], "category": "storm_prep", "status": {"$ne": "completed"}})
            if existing:
                continue
            doc = {
                "id": new_id(),
                "property_id": prop["id"],
                "property_name": prop["name"],
                "title": f"Hurricane Prep — {storm_name}",
                "category": "storm_prep",
                "priority": "urgent",
                "status": "open",
                "assigned_to": staff_ids[i % len(staff_ids)] if staff_ids else None,
                "notes": "Storm prep checklist dispatched.",
                "checklist": [{"text": c, "done": False} for c in STORM_CHECKLIST],
                "cost": 0.0,
                "predictive": False,
                "storm": True,
                "before_photo": None,
                "after_photo": None,
                "created_at": now_iso(),
                "completed_at": None,
            }
            await db.maintenance.insert_one(doc)
    return await db.storm.find_one({"id": "global"}, {"_id": 0})


# ---------------------------------------------------------------------------
# Owner portal — financials & holds
# ---------------------------------------------------------------------------
@api.get("/owner/financials")
async def owner_financials(user: dict = Depends(get_current_user)):
    if user["role"] == "owner":
        owner_id = user["id"]
    else:
        owner_id = None
    q = {} if owner_id is None else {"owner_id": owner_id}
    ledgers = await db.ledgers.find(q, {"_id": 0}).to_list(2000)

    monthly = {}
    total_owner = total_commission = total_cleaning = total_tax = total_gross = 0.0
    for l in ledgers:
        m = l["month"]
        monthly.setdefault(m, {"month": m, "revenue": 0.0, "owner_payout": 0.0, "expenses": 0.0})
        monthly[m]["revenue"] += l["gross"]
        monthly[m]["owner_payout"] += l["owner_payout"]
        monthly[m]["expenses"] += l["maintenance_cost"]
        total_gross += l["gross"]
        total_owner += l["owner_payout"]
        total_commission += l["commission"]
        total_cleaning += l["cleaning_fee"]
        total_tax += l["occupancy_tax"]

    months_sorted = sorted(monthly.values(), key=lambda x: x["month"])
    return {
        "summary": {
            "gross_revenue": round(total_gross, 2),
            "owner_payout": round(total_owner, 2),
            "commission": round(total_commission, 2),
            "cleaning_fees": round(total_cleaning, 2),
            "occupancy_tax": round(total_tax, 2),
            "roi": round((total_owner / total_gross * 100) if total_gross else 0, 1),
        },
        "monthly": months_sorted,
        "ledgers": sorted(ledgers, key=lambda x: x["date"], reverse=True),
    }


@api.get("/owner/holds")
async def list_holds(user: dict = Depends(get_current_user)):
    q = {}
    if user["role"] == "owner":
        owned = await db.properties.find({"owner_id": user["id"]}, {"id": 1, "_id": 0}).to_list(200)
        q = {"property_id": {"$in": [p["id"] for p in owned]}}
    holds = await db.holds.find(q, {"_id": 0}).sort("start_date", 1).to_list(200)
    return holds


@api.post("/owner/holds")
async def create_hold(inp: OwnerHoldCreate, user: dict = Depends(get_current_user)):
    prop = await db.properties.find_one({"id": inp.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    doc = {
        "id": new_id(),
        "property_id": inp.property_id,
        "property_name": prop["name"],
        "owner_id": user["id"],
        "start_date": inp.start_date,
        "end_date": inp.end_date,
        "note": inp.note,
        "created_at": now_iso(),
    }
    await db.holds.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.delete("/owner/holds/{hid}")
async def delete_hold(hid: str, user: dict = Depends(get_current_user)):
    await db.holds.delete_one({"id": hid})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Trust accounting
# ---------------------------------------------------------------------------
@api.get("/accounting/ledger")
async def accounting_ledger(user: dict = Depends(require_roles("manager"))):
    ledgers = await db.ledgers.find({}, {"_id": 0}).sort("date", -1).to_list(2000)
    totals = {"gross": 0.0, "owner_payout": 0.0, "commission": 0.0, "cleaning_fee": 0.0, "occupancy_tax": 0.0}
    for l in ledgers:
        for k in totals:
            totals[k] += l.get(k, 0.0)
    totals = {k: round(v, 2) for k, v in totals.items()}
    return {"ledgers": ledgers, "totals": totals}


# ---------------------------------------------------------------------------
# Communications hub
# ---------------------------------------------------------------------------
@api.get("/inbox")
async def list_threads(user: dict = Depends(get_current_user)):
    threads = await db.threads.find({}, {"_id": 0}).sort("last_at", -1).to_list(200)
    return threads


@api.get("/inbox/{tid}")
async def get_thread(tid: str, user: dict = Depends(get_current_user)):
    thread = await db.threads.find_one({"id": tid}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@api.post("/inbox/{tid}/message")
async def send_message(tid: str, inp: MessageInput, user: dict = Depends(get_current_user)):
    thread = await db.threads.find_one({"id": tid})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    msg = {"id": new_id(), "from": "host", "body": inp.body, "at": now_iso()}
    messages = thread.get("messages", [])
    messages.append(msg)
    await db.threads.update_one(
        {"id": tid},
        {"$set": {"messages": messages, "last_at": now_iso(), "preview": inp.body[:80], "unread": False}},
    )
    return await db.threads.find_one({"id": tid}, {"_id": 0})


# ---------------------------------------------------------------------------
# AI endpoints
# ---------------------------------------------------------------------------
@api.post("/ai/draft-reply")
async def ai_draft_reply(inp: AIReplyInput, user: dict = Depends(get_current_user)):
    thread = await db.threads.find_one({"id": inp.thread_id}, {"_id": 0})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    convo = "\n".join([f'{m["from"]}: {m["body"]}' for m in thread.get("messages", [])[-6:]])
    system = (
        "You are a friendly, professional vacation-rental host assistant for a Southeast US "
        "coastal property management company. Draft ONE concise, warm reply (2-4 sentences) to the "
        "guest's latest message. Be specific to coastal Florida/Carolina/Alabama context when relevant "
        "(beach access, pool heating, hurricane cancellation policy). Return only the reply text."
    )
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"reply-{inp.thread_id}", system_message=system).with_model("openai", "gpt-5.4")
    try:
        reply = await chat.send_message(UserMessage(text=f"Property: {thread.get('property_name')}\nChannel: {thread.get('channel')}\nConversation:\n{convo}\n\nDraft the host's reply:"))
    except Exception as e:
        logger.exception("AI draft failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"draft": reply.strip() if isinstance(reply, str) else str(reply)}


@api.post("/ai/translate")
async def ai_translate(inp: TranslateInput, user: dict = Depends(get_current_user)):
    target_lang = "Spanish" if inp.target == "es" else "English"
    system = f"You are a translator. Translate the user's text to {target_lang}. Return only the translation, no quotes or notes."
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="translate", system_message=system).with_model("openai", "gpt-5.4-mini")
    try:
        out = await chat.send_message(UserMessage(text=inp.text))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"translation": out.strip() if isinstance(out, str) else str(out)}


# ---------------------------------------------------------------------------
# Reservations & Central Calendar
# ---------------------------------------------------------------------------
async def _check_availability(property_id: str, check_in: str, check_out: str):
    overlap = await db.bookings.find_one({
        "property_id": property_id,
        "status": {"$ne": "cancelled"},
        "check_in": {"$lt": check_out},
        "check_out": {"$gt": check_in},
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Dates overlap an existing reservation")
    holds = await db.holds.find({"property_id": property_id}, {"_id": 0}).to_list(500)
    for h in holds:
        if h["start_date"][:10] < check_out and h["end_date"][:10] > check_in:
            raise HTTPException(status_code=409, detail="Dates overlap an owner hold")


async def _create_booking_record(prop, guest_name, guest_email, guest_phone, check_in, check_out, channel, nightly=None):
    nights = nights_between(check_in, check_out)
    if nights < 1:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    await _check_availability(prop["id"], check_in, check_out)

    nightly = nightly if nightly is not None else prop.get("nightly", 250)
    cleaning_fee = prop.get("cleaning_fee", 150)
    splits = compute_splits(nightly, nights, cleaning_fee)

    guest = await db.guests.find_one({"name": guest_name})
    if guest:
        gid = guest["id"]
        await db.guests.update_one({"id": gid}, {"$set": {
            "email": guest_email or guest.get("email"),
            "phone": guest_phone or guest.get("phone"),
        }})
    else:
        gid = new_id()
        await db.guests.insert_one({
            "id": gid, "name": guest_name, "email": guest_email,
            "phone": guest_phone, "notes": "", "created_at": now_iso(),
        })

    bid = new_id()
    month = check_in[:7]
    booking = {
        "id": bid, "property_id": prop["id"], "property_name": prop["name"],
        "owner_id": prop["owner_id"], "guest_id": gid, "guest_name": guest_name,
        "channel": channel, "check_in": check_in, "check_out": check_out,
        "nights": nights, "nightly": nightly, "status": "confirmed",
        "month": month, "created_at": now_iso(), **splits,
    }
    await db.bookings.insert_one(dict(booking))
    await db.ledgers.insert_one({
        "id": new_id(), "booking_id": bid, "property_id": prop["id"], "property_name": prop["name"],
        "owner_id": prop["owner_id"], "month": month, "date": check_in + "T00:00:00+00:00",
        "channel": channel, "nights": nights, **splits,
    })
    await db.housekeeping.insert_one({
        "id": new_id(), "property_id": prop["id"], "property_name": prop["name"],
        "image": prop["image"], "assigned_to": None,
        "turnover_date": check_out + "T11:00:00+00:00",
        "status": "pending", "photos": [],
        "checkout_guest": guest_name, "booking_id": bid, "created_at": now_iso(),
    })
    booking.pop("_id", None)
    return booking


@api.get("/bookings")
async def list_bookings(user: dict = Depends(get_current_user)):
    q = {}
    if user["role"] == "owner":
        owned = await db.properties.find({"owner_id": user["id"]}, {"id": 1, "_id": 0}).to_list(200)
        q = {"property_id": {"$in": [p["id"] for p in owned]}}
    bookings = await db.bookings.find(q, {"_id": 0}).sort("check_in", 1).to_list(2000)
    return bookings


@api.post("/bookings")
async def create_booking(inp: BookingCreate, user: dict = Depends(require_roles("manager"))):
    prop = await db.properties.find_one({"id": inp.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return await _create_booking_record(
        prop, inp.guest_name, inp.guest_email, inp.guest_phone,
        inp.check_in, inp.check_out, inp.channel, inp.nightly,
    )


@api.patch("/bookings/{bid}")
async def update_booking(bid: str, inp: BookingStatusUpdate, user: dict = Depends(require_roles("manager"))):
    booking = await db.bookings.find_one({"id": bid})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    await db.bookings.update_one({"id": bid}, {"$set": {"status": inp.status}})
    if inp.status == "cancelled":
        await db.ledgers.delete_many({"booking_id": bid})
    return await db.bookings.find_one({"id": bid}, {"_id": 0})


@api.get("/calendar")
async def calendar(user: dict = Depends(get_current_user)):
    props = await db.properties.find({}, {"_id": 0}).to_list(200)
    bookings = await db.bookings.find({"status": {"$ne": "cancelled"}}, {"_id": 0}).to_list(2000)
    holds = await db.holds.find({}, {"_id": 0}).to_list(500)
    return {"properties": props, "bookings": bookings, "holds": holds}


# ---------------------------------------------------------------------------
# Guest CRM
# ---------------------------------------------------------------------------
@api.get("/guests")
async def list_guests(user: dict = Depends(require_roles("manager"))):
    guests = await db.guests.find({}, {"_id": 0}).to_list(1000)
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(2000)
    by_guest = {}
    for b in bookings:
        g = by_guest.setdefault(b["guest_id"], {"stays": 0, "spent": 0.0, "last": None})
        g["stays"] += 1
        g["spent"] += b["gross"]
        if not g["last"] or b["check_in"] > g["last"]:
            g["last"] = b["check_in"]
    for g in guests:
        agg = by_guest.get(g["id"], {"stays": 0, "spent": 0.0, "last": None})
        g["total_stays"] = agg["stays"]
        g["total_spent"] = round(agg["spent"], 2)
        g["last_stay"] = agg["last"]
    guests.sort(key=lambda x: x["total_spent"], reverse=True)
    return guests


@api.get("/guests/{gid}")
async def guest_detail(gid: str, user: dict = Depends(require_roles("manager"))):
    guest = await db.guests.find_one({"id": gid}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    stays = await db.bookings.find({"guest_id": gid}, {"_id": 0}).sort("check_in", -1).to_list(200)
    guest["stays"] = stays
    guest["total_stays"] = len(stays)
    guest["total_spent"] = round(sum(s["gross"] for s in stays), 2)
    return guest


@api.patch("/guests/{gid}")
async def update_guest(gid: str, payload: dict, user: dict = Depends(require_roles("manager"))):
    await db.guests.update_one({"id": gid}, {"$set": {"notes": payload.get("notes", "")}})
    return await db.guests.find_one({"id": gid}, {"_id": 0})


# ---------------------------------------------------------------------------
# Reporting & Analytics
# ---------------------------------------------------------------------------
@api.get("/reports/analytics")
async def analytics(user: dict = Depends(require_roles("manager"))):
    props = await db.properties.find({}, {"_id": 0}).to_list(200)
    bookings = await db.bookings.find({"status": {"$ne": "cancelled"}}, {"_id": 0}).to_list(3000)

    n_props = max(1, len(props))
    total_nights = sum(b["nights"] for b in bookings)
    total_gross = sum(b["gross"] for b in bookings)
    n_bookings = max(1, len(bookings))

    # occupancy over a 180-day window
    window_days = 180
    available_nights = n_props * window_days
    occupancy = round(min(100.0, total_nights / max(1, available_nights) * 100), 1)
    adr = round(total_gross / max(1, total_nights), 2)            # avg daily rate
    revpar = round(total_gross / max(1, available_nights), 2)     # revenue per available room-night
    avg_los = round(total_nights / n_bookings, 1)                 # length of stay

    # by channel
    channel = {}
    for b in bookings:
        c = channel.setdefault(b["channel"], {"name": b["channel"], "revenue": 0.0, "bookings": 0})
        c["revenue"] += b["gross"]
        c["bookings"] += 1
    channels = [{"name": k, "revenue": round(v["revenue"], 2), "bookings": v["bookings"]} for k, v in channel.items()]

    # by property
    by_prop = {}
    for b in bookings:
        p = by_prop.setdefault(b["property_id"], {"name": b["property_name"], "revenue": 0.0, "nights": 0})
        p["revenue"] += b["gross"]
        p["nights"] += b["nights"]
    properties = [{
        "name": v["name"], "revenue": round(v["revenue"], 2),
        "occupancy": round(min(100.0, v["nights"] / window_days * 100), 1),
    } for v in by_prop.values()]
    properties.sort(key=lambda x: x["revenue"], reverse=True)

    # monthly revenue trend
    monthly = {}
    for b in bookings:
        monthly[b["month"]] = monthly.get(b["month"], 0.0) + b["gross"]
    monthly_list = [{"month": k, "revenue": round(v, 2)} for k, v in sorted(monthly.items())]

    return {
        "kpis": {
            "occupancy": occupancy, "adr": adr, "revpar": revpar,
            "avg_los": avg_los, "total_revenue": round(total_gross, 2), "bookings": len(bookings),
        },
        "channels": channels,
        "properties": properties,
        "monthly": monthly_list,
    }


# ---------------------------------------------------------------------------
# Owner statement
# ---------------------------------------------------------------------------
@api.get("/owner/statement")
async def owner_statement(month: Optional[str] = None, user: dict = Depends(get_current_user)):
    owner_id = user["id"] if user["role"] == "owner" else None
    q = {} if owner_id is None else {"owner_id": owner_id}
    ledgers = await db.ledgers.find(q, {"_id": 0}).to_list(3000)
    months = sorted({l["month"] for l in ledgers}, reverse=True)
    if not month:
        month = months[0] if months else None
    rows = [l for l in ledgers if l["month"] == month]

    by_prop = {}
    totals = {"gross": 0.0, "commission": 0.0, "occupancy_tax": 0.0, "cleaning_fee": 0.0, "maintenance_cost": 0.0, "owner_payout": 0.0}
    for r in rows:
        p = by_prop.setdefault(r["property_id"], {"property_name": r["property_name"], "gross": 0.0, "commission": 0.0, "occupancy_tax": 0.0, "maintenance_cost": 0.0, "owner_payout": 0.0, "bookings": 0})
        for k in ["gross", "commission", "occupancy_tax", "maintenance_cost", "owner_payout"]:
            p[k] += r.get(k, 0.0)
        p["bookings"] += 1
        for k in totals:
            totals[k] += r.get(k, 0.0)
    totals = {k: round(v, 2) for k, v in totals.items()}
    properties = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items()} for p in by_prop.values()]

    owner = await db.users.find_one({"id": (owner_id or rows[0]["owner_id"]) if rows else owner_id}, {"_id": 0, "password_hash": 0}) if (owner_id or rows) else None
    return {
        "month": month, "available_months": months,
        "owner_name": owner["name"] if owner else "All Owners",
        "properties": properties, "totals": totals,
    }


# ---------------------------------------------------------------------------
# Rates & pricing
# ---------------------------------------------------------------------------
@api.patch("/properties/{pid}/rates")
async def update_rates(pid: str, inp: RatesUpdate, user: dict = Depends(require_roles("manager"))):
    prop = await db.properties.find_one({"id": pid})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    updates = {k: v for k, v in inp.model_dump().items() if v is not None}
    await db.properties.update_one({"id": pid}, {"$set": updates})
    return await db.properties.find_one({"id": pid}, {"_id": 0})


# ---------------------------------------------------------------------------
# Public direct-booking website + Stripe checkout
# ---------------------------------------------------------------------------
def guest_total(prop, nights):
    splits = compute_splits(prop.get("nightly", 250), nights, prop.get("cleaning_fee", 150))
    total = round(splits["gross"] + splits["cleaning_fee"] + splits["occupancy_tax"], 2)
    return splits, total


@api.get("/public/properties")
async def public_properties():
    props = await db.properties.find({}, {"_id": 0, "owner_id": 0, "owner_name": 0, "occupancy": 0}).to_list(200)
    return props


@api.get("/public/quote")
async def public_quote(property_id: str, check_in: str, check_out: str):
    prop = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    nights = nights_between(check_in, check_out)
    if nights < 1:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    splits, total = guest_total(prop, nights)
    # availability (does not raise — returns flag)
    available = True
    try:
        await _check_availability(property_id, check_in, check_out)
    except HTTPException:
        available = False
    return {
        "property_name": prop["name"], "nights": nights, "nightly": prop["nightly"],
        "accommodation": splits["gross"], "cleaning_fee": splits["cleaning_fee"],
        "occupancy_tax": splits["occupancy_tax"], "total": total, "available": available,
    }


@api.post("/public/checkout")
async def public_checkout(inp: CheckoutInput, request: Request):
    prop = await db.properties.find_one({"id": inp.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    nights = nights_between(inp.check_in, inp.check_out)
    if nights < 1:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    # block clearly unavailable dates up front
    await _check_availability(inp.property_id, inp.check_in, inp.check_out)

    _, total = guest_total(prop, nights)  # amount computed server-side ONLY

    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    origin = inp.origin_url.rstrip("/")
    success_url = f"{origin}/book/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/book"

    metadata = {
        "type": "booking",
        "property_id": inp.property_id,
        "guest_name": inp.guest_name,
        "guest_email": inp.guest_email,
        "check_in": inp.check_in,
        "check_out": inp.check_out,
    }
    req = CheckoutSessionRequest(
        amount=float(total), currency="usd",
        success_url=success_url, cancel_url=cancel_url, metadata=metadata,
    )
    session = await stripe_checkout.create_checkout_session(req)

    await db.payment_transactions.insert_one({
        "id": new_id(), "session_id": session.session_id,
        "amount": float(total), "currency": "usd",
        "status": "initiated", "payment_status": "pending",
        "metadata": metadata, "booking_id": None,
        "created_at": now_iso(), "updated_at": now_iso(),
    })
    return {"url": session.url, "session_id": session.session_id}


async def _finalize_payment(session_id: str, status: str, payment_status: str):
    """Idempotently update the transaction and create the booking on first paid."""
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        return None
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status, "payment_status": payment_status, "updated_at": now_iso()}},
    )
    if payment_status == "paid" and not txn.get("booking_id"):
        meta = txn.get("metadata", {})
        prop = await db.properties.find_one({"id": meta.get("property_id")}, {"_id": 0})
        if prop:
            try:
                booking = await _create_booking_record(
                    prop, meta.get("guest_name"), meta.get("guest_email"), None,
                    meta.get("check_in"), meta.get("check_out"), "Direct",
                )
                await db.payment_transactions.update_one(
                    {"session_id": session_id}, {"$set": {"booking_id": booking["id"]}}
                )
                return booking
            except HTTPException:
                # dates became unavailable between checkout and payment — flag for refund handling
                await db.payment_transactions.update_one(
                    {"session_id": session_id}, {"$set": {"status": "needs_review"}}
                )
    return None


@api.get("/public/checkout/status/{session_id}")
async def public_checkout_status(session_id: str, request: Request):
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.get("payment_status") != "paid":
        host_url = str(request.base_url)
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{host_url}api/webhook/stripe")
        result: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        await _finalize_payment(session_id, result.status, result.payment_status)
        txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    booking = None
    if txn.get("booking_id"):
        booking = await db.bookings.find_one({"id": txn["booking_id"]}, {"_id": 0})
    return {
        "status": txn["status"], "payment_status": txn["payment_status"],
        "amount": txn["amount"], "metadata": txn.get("metadata", {}), "booking": booking,
    }


@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    host_url = str(request.base_url)
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{host_url}api/webhook/stripe")
    try:
        event = await stripe_checkout.handle_webhook(body, sig)
        await _finalize_payment(event.session_id, "complete", event.payment_status)
    except Exception as e:
        logger.exception("Stripe webhook error")
        raise HTTPException(status_code=400, detail=str(e))
    return {"received": True}


# ---------------------------------------------------------------------------
# Manager dashboard summary
# ---------------------------------------------------------------------------
@api.get("/dashboard/summary")
async def dashboard_summary(user: dict = Depends(get_current_user)):
    props = await db.properties.count_documents({})
    open_maint = await db.maintenance.count_documents({"status": {"$ne": "completed"}})
    storm_tasks = await db.maintenance.count_documents({"category": "storm_prep", "status": {"$ne": "completed"}})
    hk_pending = await db.housekeeping.count_documents({"status": {"$ne": "guest_ready"}})
    ledgers = await db.ledgers.find({}, {"_id": 0}).to_list(5000)
    mtd = sum(l["gross"] for l in ledgers)
    payouts = sum(l["owner_payout"] for l in ledgers)
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming = await db.bookings.count_documents({"check_in": {"$gte": today}, "status": {"$ne": "cancelled"}})
    storm = await db.storm.find_one({"id": "global"}, {"_id": 0})
    return {
        "properties": props,
        "open_maintenance": open_maint,
        "storm_tasks": storm_tasks,
        "housekeeping_pending": hk_pending,
        "revenue": round(mtd, 2),
        "owner_payouts": round(payouts, 2),
        "upcoming_bookings": upcoming,
        "storm_active": bool(storm and storm.get("active")),
        "storm_name": storm.get("storm_name") if storm else None,
    }


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id")
    from seed import seed_all
    await seed_all(db)


@app.on_event("shutdown")
async def shutdown():
    client.close()
