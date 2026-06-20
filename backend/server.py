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

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']

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
# Manager dashboard summary
# ---------------------------------------------------------------------------
@api.get("/dashboard/summary")
async def dashboard_summary(user: dict = Depends(get_current_user)):
    props = await db.properties.count_documents({})
    open_maint = await db.maintenance.count_documents({"status": {"$ne": "completed"}})
    storm_tasks = await db.maintenance.count_documents({"category": "storm_prep", "status": {"$ne": "completed"}})
    hk_pending = await db.housekeeping.count_documents({"status": {"$ne": "guest_ready"}})
    ledgers = await db.ledgers.find({}, {"_id": 0}).to_list(2000)
    mtd = sum(l["gross"] for l in ledgers)
    payouts = sum(l["owner_payout"] for l in ledgers)
    storm = await db.storm.find_one({"id": "global"}, {"_id": 0})
    return {
        "properties": props,
        "open_maintenance": open_maint,
        "storm_tasks": storm_tasks,
        "housekeeping_pending": hk_pending,
        "revenue": round(mtd, 2),
        "owner_payouts": round(payouts, 2),
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
