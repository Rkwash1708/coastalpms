"""Comprehensive Coastline PMS API tests covering auth, properties, maintenance,
housekeeping, storm mode, owner portal, trust accounting, inbox, AI endpoints,
and dashboard summary."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://coastal-ops.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "manager": ("manager@coastline.com", "Manager123"),
    "housekeeper": ("maria@coastline.com", "Field123"),
    "maintenance": ("carlos@coastline.com", "Field123"),
    "owner": ("owner@coastline.com", "Owner123"),
}


# ------------------------- Fixtures -------------------------
@pytest.fixture(scope="session")
def tokens():
    out = {}
    for role, (email, pw) in CREDS.items():
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
        assert r.status_code == 200, f"login {role} failed: {r.status_code} {r.text}"
        out[role] = r.json()["token"]
    return out


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ------------------------- Auth -------------------------
class TestAuth:
    def test_login_manager(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["manager"][0], "password": CREDS["manager"][1]}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["role"] == "manager"
        assert "token" in d and len(d["token"]) > 20

    def test_login_housekeeper(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["housekeeper"][0], "password": CREDS["housekeeper"][1]}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "housekeeper"

    def test_login_maintenance(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["maintenance"][0], "password": CREDS["maintenance"][1]}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "maintenance"

    def test_login_owner(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["owner"][0], "password": CREDS["owner"][1]}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "owner"

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "manager@coastline.com", "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = requests.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 401

    def test_me_with_token(self, tokens):
        r = requests.get(f"{API}/auth/me", headers=auth_headers(tokens["manager"]), timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == CREDS["manager"][0]
        assert "password_hash" not in r.json()


# ------------------------- Properties -------------------------
class TestProperties:
    def test_list_manager_sees_all(self, tokens):
        r = requests.get(f"{API}/properties", headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        props = r.json()
        assert isinstance(props, list)
        assert len(props) >= 6, f"expected >=6 seeded properties, got {len(props)}"

    def test_list_owner_filtered(self, tokens):
        r = requests.get(f"{API}/properties", headers=auth_headers(tokens["owner"]), timeout=15)
        assert r.status_code == 200
        props = r.json()
        assert isinstance(props, list)
        # Owner should see at least their properties; could be subset
        assert all("owner_id" in p for p in props)


# ------------------------- Dashboard -------------------------
class TestDashboard:
    def test_summary(self, tokens):
        r = requests.get(f"{API}/dashboard/summary", headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("properties", "open_maintenance", "storm_tasks", "housekeeping_pending", "revenue", "owner_payouts"):
            assert k in d
        assert d["properties"] >= 6


# ------------------------- Maintenance -------------------------
class TestMaintenance:
    def test_list_manager(self, tokens):
        r = requests.get(f"{API}/maintenance", headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_maintenance_role(self, tokens):
        r = requests.get(f"{API}/maintenance", headers=auth_headers(tokens["maintenance"]), timeout=15)
        assert r.status_code == 200

    def test_create_and_update_task(self, tokens):
        # Pick a property
        props = requests.get(f"{API}/properties", headers=auth_headers(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        payload = {"property_id": pid, "title": "TEST_AC_filter_change", "category": "hvac", "priority": "normal", "cost": 75.0}
        r = requests.post(f"{API}/maintenance", json=payload, headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200, r.text
        task = r.json()
        assert task["title"] == "TEST_AC_filter_change"
        assert task["status"] == "open"
        tid = task["id"]

        # Patch: complete + after photo
        upd = {"status": "completed", "after": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEX/AAAZ4gk3AAAAAXRSTlMAQObYZgAAAApJREFUCNdjYAAAAAIAAeIhvDMAAAAASUVORK5CYII="}
        r2 = requests.patch(f"{API}/maintenance/{tid}", json=upd, headers=auth_headers(tokens["manager"]), timeout=15)
        assert r2.status_code == 200
        assert r2.json()["status"] == "completed"
        assert r2.json()["after_photo"] is not None
        assert r2.json()["completed_at"] is not None

    def test_predictive_tasks_present(self, tokens):
        r = requests.get(f"{API}/maintenance", headers=auth_headers(tokens["manager"]), timeout=15)
        tasks = r.json()
        predictive = [t for t in tasks if t.get("predictive")]
        assert len(predictive) > 0, "expected at least one predictive maintenance task in seed"


# ------------------------- Housekeeping -------------------------
class TestHousekeeping:
    def test_list(self, tokens):
        r = requests.get(f"{API}/housekeeping", headers=auth_headers(tokens["housekeeper"]), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_guest_ready_flow(self, tokens):
        tasks = requests.get(f"{API}/housekeeping", headers=auth_headers(tokens["housekeeper"]), timeout=15).json()
        assert len(tasks) > 0, "expected housekeeping seed tasks"
        tid = tasks[0]["id"]
        photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEX/AAAZ4gk3AAAAAXRSTlMAQObYZgAAAApJREFUCNdjYAAAAAIAAeIhvDMAAAAASUVORK5CYII="
        r = requests.post(f"{API}/housekeeping/{tid}/guest-ready", json={"photo": photo}, headers=auth_headers(tokens["housekeeper"]), timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "guest_ready"
        assert any(p.get("url") for p in d.get("photos", []))


# ------------------------- Storm Mode -------------------------
class TestStorm:
    def test_storm_status(self, tokens):
        r = requests.get(f"{API}/storm/status", headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        assert "active" in r.json()

    def test_storm_activate_manager_only(self, tokens):
        # Non-manager forbidden
        r_o = requests.post(f"{API}/storm/activate", json={"storm_name": "TEST_BlockMe", "active": True}, headers=auth_headers(tokens["owner"]), timeout=15)
        assert r_o.status_code == 403

        # Manager: activate
        r = requests.post(f"{API}/storm/activate", json={"storm_name": "TEST_Hermine", "active": True}, headers=auth_headers(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        assert r.json()["active"] is True
        assert r.json()["storm_name"] == "TEST_Hermine"

        # Verify hurricane prep tasks created
        tasks = requests.get(f"{API}/maintenance", headers=auth_headers(tokens["manager"]), timeout=15).json()
        storm_tasks = [t for t in tasks if t.get("category") == "storm_prep" and t.get("status") != "completed"]
        assert len(storm_tasks) > 0, "expected hurricane prep tasks after activation"

        # Stand down
        r2 = requests.post(f"{API}/storm/activate", json={"storm_name": "", "active": False}, headers=auth_headers(tokens["manager"]), timeout=15)
        assert r2.status_code == 200
        assert r2.json()["active"] is False


# ------------------------- Owner Portal -------------------------
class TestOwnerPortal:
    def test_financials(self, tokens):
        r = requests.get(f"{API}/owner/financials", headers=auth_headers(tokens["owner"]), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "summary" in d and "monthly" in d and "ledgers" in d
        s = d["summary"]
        for k in ("gross_revenue", "owner_payout", "commission", "cleaning_fees", "occupancy_tax", "roi"):
            assert k in s

    def test_holds_create_list_delete(self, tokens):
        props = requests.get(f"{API}/properties", headers=auth_headers(tokens["owner"]), timeout=15).json()
        assert len(props) > 0, "owner has no properties"
        pid = props[0]["id"]
        payload = {"property_id": pid, "start_date": "2026-03-15", "end_date": "2026-03-20", "note": "TEST_family_trip"}
        r = requests.post(f"{API}/owner/holds", json=payload, headers=auth_headers(tokens["owner"]), timeout=15)
        assert r.status_code == 200
        hid = r.json()["id"]
        r2 = requests.get(f"{API}/owner/holds", headers=auth_headers(tokens["owner"]), timeout=15)
        assert r2.status_code == 200
        assert any(h["id"] == hid for h in r2.json())
        r3 = requests.delete(f"{API}/owner/holds/{hid}", headers=auth_headers(tokens["owner"]), timeout=15)
        assert r3.status_code == 200


# ------------------------- Trust Accounting -------------------------
class TestAccounting:
    def test_ledger_manager(self, tokens):
        r = requests.get(f"{API}/accounting/ledger", headers=auth_headers(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "ledgers" in d and "totals" in d
        assert len(d["ledgers"]) > 50, f"expected ~106 ledger rows, got {len(d['ledgers'])}"
        for k in ("gross", "owner_payout", "commission", "cleaning_fee", "occupancy_tax"):
            assert k in d["totals"]

    def test_ledger_blocked_owner(self, tokens):
        r = requests.get(f"{API}/accounting/ledger", headers=auth_headers(tokens["owner"]), timeout=15)
        assert r.status_code == 403


# ------------------------- Inbox -------------------------
class TestInbox:
    def test_list_threads(self, tokens):
        r = requests.get(f"{API}/inbox", headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_send_message(self, tokens):
        threads = requests.get(f"{API}/inbox", headers=auth_headers(tokens["manager"]), timeout=15).json()
        tid = threads[0]["id"]
        r = requests.post(f"{API}/inbox/{tid}/message", json={"body": "TEST_reply from automated test"}, headers=auth_headers(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        msgs = r.json()["messages"]
        assert any(m["body"] == "TEST_reply from automated test" for m in msgs)


# ------------------------- AI -------------------------
class TestAI:
    def test_ai_draft_reply(self, tokens):
        threads = requests.get(f"{API}/inbox", headers=auth_headers(tokens["manager"]), timeout=15).json()
        tid = threads[0]["id"]
        r = requests.post(f"{API}/ai/draft-reply", json={"thread_id": tid}, headers=auth_headers(tokens["manager"]), timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "draft" in d and len(d["draft"]) > 10

    def test_ai_translate(self, tokens):
        r = requests.post(f"{API}/ai/translate", json={"text": "Welcome to the beach house", "target": "es"}, headers=auth_headers(tokens["manager"]), timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert "translation" in d and len(d["translation"]) > 0
