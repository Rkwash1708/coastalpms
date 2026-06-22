"""Iteration 2 tests: Bookings, Calendar, Guests CRM, Reports/Analytics,
Owner Statement, Rates/Pricing, and dashboard upcoming_bookings."""
import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "manager": ("manager@coastline.com", "Manager123"),
    "owner": ("owner@coastline.com", "Owner123"),
}


@pytest.fixture(scope="module")
def tokens():
    out = {}
    for role, (email, pw) in CREDS.items():
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=20)
        assert r.status_code == 200, f"login {role}: {r.text}"
        out[role] = r.json()["token"]
    return out


def H(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ------------- Bookings + Calendar -------------
class TestBookings:
    def test_list_bookings_manager(self, tokens):
        r = requests.get(f"{API}/bookings", headers=H(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        bookings = r.json()
        assert isinstance(bookings, list)
        # ~107 seeded
        assert len(bookings) >= 50, f"expected seeded bookings, got {len(bookings)}"
        # validate fields
        b = bookings[0]
        for k in ("id", "property_id", "guest_name", "check_in", "check_out", "nights", "nightly", "gross", "owner_payout", "commission", "occupancy_tax", "channel", "month"):
            assert k in b, f"missing {k} in booking"

    def test_calendar(self, tokens):
        r = requests.get(f"{API}/calendar", headers=H(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "properties" in d and "bookings" in d and "holds" in d
        assert len(d["properties"]) >= 6

    def test_create_booking_full_flow(self, tokens):
        # Pick a property
        props = requests.get(f"{API}/properties", headers=H(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        # use far future to avoid overlap with seeded data
        check_in = "2027-08-10"
        check_out = "2027-08-15"
        payload = {
            "property_id": pid, "guest_name": "TEST_Guest_Iter2",
            "guest_email": "test.iter2@example.com",
            "check_in": check_in, "check_out": check_out,
            "channel": "Direct",
        }
        # snapshot ledger & housekeeping counts
        led_before = requests.get(f"{API}/accounting/ledger", headers=H(tokens["manager"]), timeout=20).json()
        hk_before = requests.get(f"{API}/housekeeping", headers=H(tokens["manager"]), timeout=20).json()

        r = requests.post(f"{API}/bookings", json=payload, headers=H(tokens["manager"]), timeout=20)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b["status"] == "confirmed"
        assert b["nights"] == 5
        assert b["guest_name"] == "TEST_Guest_Iter2"
        assert b["gross"] > 0
        # splits sanity (gross == owner_payout + commission + occupancy_tax)
        s = round(b["owner_payout"] + b["commission"] + b["occupancy_tax"], 2)
        assert abs(s - b["gross"]) < 0.05, f"split mismatch: {b}"
        bid = b["id"]

        # GET verifies persistence in list
        listed = requests.get(f"{API}/bookings", headers=H(tokens["manager"]), timeout=20).json()
        assert any(x["id"] == bid for x in listed)

        # auto-ledger created
        led_after = requests.get(f"{API}/accounting/ledger", headers=H(tokens["manager"]), timeout=20).json()
        assert len(led_after["ledgers"]) == len(led_before["ledgers"]) + 1
        new_l = [l for l in led_after["ledgers"] if l.get("booking_id") == bid]
        assert len(new_l) == 1, "expected one auto-ledger for new booking"
        assert new_l[0]["gross"] == b["gross"]

        # auto-housekeeping turnover
        hk_after = requests.get(f"{API}/housekeeping", headers=H(tokens["manager"]), timeout=20).json()
        assert len(hk_after) == len(hk_before) + 1
        new_hk = [h for h in hk_after if h.get("booking_id") == bid]
        assert len(new_hk) == 1
        assert new_hk[0]["status"] == "pending"
        assert new_hk[0]["checkout_guest"] == "TEST_Guest_Iter2"

    def test_overlap_returns_409(self, tokens):
        props = requests.get(f"{API}/properties", headers=H(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        # First booking
        payload1 = {
            "property_id": pid, "guest_name": "TEST_Overlap_A",
            "check_in": "2027-09-01", "check_out": "2027-09-05", "channel": "Direct",
        }
        r1 = requests.post(f"{API}/bookings", json=payload1, headers=H(tokens["manager"]), timeout=20)
        assert r1.status_code == 200, r1.text
        # overlapping window
        payload2 = {
            "property_id": pid, "guest_name": "TEST_Overlap_B",
            "check_in": "2027-09-03", "check_out": "2027-09-07", "channel": "Airbnb",
        }
        r2 = requests.post(f"{API}/bookings", json=payload2, headers=H(tokens["manager"]), timeout=20)
        assert r2.status_code == 409, f"expected 409, got {r2.status_code} {r2.text}"

    def test_booking_create_requires_manager(self, tokens):
        # owner forbidden
        props = requests.get(f"{API}/properties", headers=H(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        payload = {"property_id": pid, "guest_name": "TEST_Forbidden",
                   "check_in": "2027-10-01", "check_out": "2027-10-04", "channel": "Direct"}
        r = requests.post(f"{API}/bookings", json=payload, headers=H(tokens["owner"]), timeout=15)
        assert r.status_code == 403


# ------------- Guest CRM -------------
class TestGuests:
    def test_list_guests_ranked(self, tokens):
        r = requests.get(f"{API}/guests", headers=H(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        guests = r.json()
        assert isinstance(guests, list)
        assert len(guests) >= 14, f"expected >=14 guests, got {len(guests)}"
        # sorted by total_spent desc
        spents = [g["total_spent"] for g in guests]
        assert spents == sorted(spents, reverse=True), "guests not sorted by total_spent desc"
        for g in guests[:3]:
            for k in ("id", "name", "total_stays", "total_spent"):
                assert k in g

    def test_guest_detail_and_patch(self, tokens):
        guests = requests.get(f"{API}/guests", headers=H(tokens["manager"]), timeout=20).json()
        gid = guests[0]["id"]
        r = requests.get(f"{API}/guests/{gid}", headers=H(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "stays" in d and isinstance(d["stays"], list)
        assert d["total_stays"] == len(d["stays"])

        # patch notes
        r2 = requests.patch(f"{API}/guests/{gid}", json={"notes": "TEST_vip_notes"}, headers=H(tokens["manager"]), timeout=15)
        assert r2.status_code == 200
        # GET re-verifies
        r3 = requests.get(f"{API}/guests/{gid}", headers=H(tokens["manager"]), timeout=15)
        assert r3.json().get("notes") == "TEST_vip_notes"

    def test_guests_blocked_for_owner(self, tokens):
        r = requests.get(f"{API}/guests", headers=H(tokens["owner"]), timeout=15)
        assert r.status_code == 403


# ------------- Reports/Analytics -------------
class TestReports:
    def test_analytics(self, tokens):
        r = requests.get(f"{API}/reports/analytics", headers=H(tokens["manager"]), timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ("kpis", "channels", "properties", "monthly"):
            assert k in d
        k = d["kpis"]
        for kk in ("occupancy", "adr", "revpar", "avg_los", "total_revenue", "bookings"):
            assert kk in k
        assert k["total_revenue"] > 0
        assert k["bookings"] >= 50
        assert 0 <= k["occupancy"] <= 100
        assert len(d["properties"]) >= 1
        assert len(d["monthly"]) >= 1

    def test_analytics_blocked_owner(self, tokens):
        r = requests.get(f"{API}/reports/analytics", headers=H(tokens["owner"]), timeout=15)
        assert r.status_code == 403


# ------------- Owner Statement -------------
class TestOwnerStatement:
    def test_statement_default(self, tokens):
        r = requests.get(f"{API}/owner/statement", headers=H(tokens["owner"]), timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ("month", "available_months", "properties", "totals", "owner_name"):
            assert k in d
        assert isinstance(d["available_months"], list)
        assert isinstance(d["properties"], list)
        t = d["totals"]
        for kk in ("gross", "commission", "occupancy_tax", "owner_payout"):
            assert kk in t

    def test_statement_month_switch(self, tokens):
        r = requests.get(f"{API}/owner/statement", headers=H(tokens["owner"]), timeout=20)
        months = r.json()["available_months"]
        if len(months) >= 2:
            other = months[1]
            r2 = requests.get(f"{API}/owner/statement", params={"month": other}, headers=H(tokens["owner"]), timeout=20)
            assert r2.status_code == 200
            assert r2.json()["month"] == other


# ------------- Rates -------------
class TestRates:
    def test_update_rates(self, tokens):
        props = requests.get(f"{API}/properties", headers=H(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        payload = {"nightly": 333.0, "weekend_nightly": 444.0, "min_nights": 3, "cleaning_fee": 175.0}
        r = requests.patch(f"{API}/properties/{pid}/rates", json=payload, headers=H(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["nightly"] == 333.0
        assert d["weekend_nightly"] == 444.0
        assert d["min_nights"] == 3
        assert d["cleaning_fee"] == 175.0
        # GET re-verifies
        r2 = requests.get(f"{API}/properties/{pid}", headers=H(tokens["manager"]), timeout=15)
        assert r2.json()["nightly"] == 333.0

    def test_rates_blocked_owner(self, tokens):
        props = requests.get(f"{API}/properties", headers=H(tokens["manager"]), timeout=15).json()
        pid = props[0]["id"]
        r = requests.patch(f"{API}/properties/{pid}/rates", json={"nightly": 999.0}, headers=H(tokens["owner"]), timeout=15)
        assert r.status_code == 403


# ------------- Dashboard upcoming -------------
class TestDashboardUpcoming:
    def test_dashboard_includes_upcoming(self, tokens):
        r = requests.get(f"{API}/dashboard/summary", headers=H(tokens["manager"]), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "upcoming_bookings" in d
        assert isinstance(d["upcoming_bookings"], int)
        assert d["upcoming_bookings"] >= 1
