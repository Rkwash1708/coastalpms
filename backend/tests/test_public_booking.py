"""Public direct-booking + Stripe checkout tests for Coastline PMS."""
import os
import time
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/') if os.environ.get('REACT_APP_BACKEND_URL') else "https://coastal-ops.preview.emergentagent.com"
API = f"{BASE_URL}/api"

MANAGER_EMAIL = "manager@coastline.com"
MANAGER_PASSWORD = "Manager123"

# Use far-future dates well beyond seed data
CHECK_IN = "2027-09-10"
CHECK_OUT = "2027-09-15"
GUEST_NAME = "TEST_PublicBuyer"
GUEST_EMAIL = "test_pub_buyer@example.com"


@pytest.fixture(scope="session")
def manager_token():
    r = requests.post(f"{API}/auth/login", json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"manager login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def first_property():
    r = requests.get(f"{API}/public/properties", timeout=15)
    assert r.status_code == 200
    props = r.json()
    assert isinstance(props, list) and len(props) >= 1
    return props[0]


# ----------------------- Public listing -----------------------
class TestPublicProperties:
    def test_list_no_auth(self):
        r = requests.get(f"{API}/public/properties", timeout=15)
        assert r.status_code == 200
        props = r.json()
        assert isinstance(props, list)
        assert len(props) >= 6, f"expected >=6 properties, got {len(props)}"
        p = props[0]
        # Sensitive fields should be hidden
        assert "_id" not in p
        assert "owner_id" not in p
        # Necessary public fields
        for k in ("id", "name", "address", "image", "nightly", "beds", "baths"):
            assert k in p, f"missing field {k}"


# ----------------------- Quote -----------------------
class TestQuote:
    def test_quote_breakdown(self, first_property):
        r = requests.get(
            f"{API}/public/quote",
            params={"property_id": first_property["id"], "check_in": CHECK_IN, "check_out": CHECK_OUT},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        q = r.json()
        # data assertions
        assert q["nights"] == 5
        assert q["nightly"] == first_property["nightly"]
        expected_gross = round(first_property["nightly"] * 5, 2)
        assert q["accommodation"] == expected_gross
        assert q["cleaning_fee"] > 0
        expected_tax = round(expected_gross * 0.11, 2)
        assert abs(q["occupancy_tax"] - expected_tax) < 0.01
        expected_total = round(expected_gross + q["cleaning_fee"] + q["occupancy_tax"], 2)
        assert abs(q["total"] - expected_total) < 0.01
        assert q["available"] in (True, False)

    def test_quote_invalid_dates(self, first_property):
        r = requests.get(
            f"{API}/public/quote",
            params={"property_id": first_property["id"], "check_in": "2027-09-15", "check_out": "2027-09-10"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_quote_property_not_found(self):
        r = requests.get(
            f"{API}/public/quote",
            params={"property_id": "nonexistent-xyz", "check_in": CHECK_IN, "check_out": CHECK_OUT},
            timeout=15,
        )
        assert r.status_code == 404


# ----------------------- Checkout -----------------------
class TestCheckout:
    @pytest.fixture(scope="class")
    def session_info(self, first_property):
        payload = {
            "property_id": first_property["id"],
            "guest_name": GUEST_NAME,
            "guest_email": GUEST_EMAIL,
            "check_in": CHECK_IN,
            "check_out": CHECK_OUT,
            "origin_url": "https://coastal-ops.preview.emergentagent.com",
        }
        r = requests.post(f"{API}/public/checkout", json=payload, timeout=30)
        assert r.status_code == 200, f"checkout failed: {r.text}"
        data = r.json()
        assert "url" in data and data["url"].startswith("https://")
        assert "session_id" in data and len(data["session_id"]) > 5
        # Stripe-hosted page
        assert "stripe.com" in data["url"]
        return data

    def test_checkout_creates_session(self, session_info):
        assert session_info["session_id"]

    def test_status_endpoint_returns_pending(self, session_info):
        r = requests.get(f"{API}/public/checkout/status/{session_info['session_id']}", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # before payment, payment_status should not be paid
        assert data["payment_status"] in ("pending", "unpaid", "no_payment_required")
        assert data["booking"] is None
        assert data["amount"] > 0
        assert data["metadata"]["guest_name"] == GUEST_NAME

    def test_status_polling_idempotent(self, session_info):
        # Hit status endpoint multiple times — no duplicate booking creation
        for _ in range(3):
            r = requests.get(f"{API}/public/checkout/status/{session_info['session_id']}", timeout=30)
            assert r.status_code == 200
            assert r.json()["booking"] is None  # still unpaid
            time.sleep(0.3)

    def test_status_not_found(self):
        r = requests.get(f"{API}/public/checkout/status/cs_test_does_not_exist", timeout=15)
        assert r.status_code == 404

    def test_checkout_overlap_returns_409(self, first_property, manager_token):
        """Create a manager booking, then attempt public checkout overlapping → 409."""
        # First create a manager booking on far-future dates
        bk = {
            "property_id": first_property["id"],
            "guest_name": "TEST_OverlapGuest",
            "guest_email": "overlap@example.com",
            "check_in": "2027-11-01",
            "check_out": "2027-11-06",
            "channel": "Direct",
        }
        r = requests.post(f"{API}/bookings", json=bk,
                          headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200, r.text
        booking_id = r.json()["id"]

        try:
            # Attempt overlapping checkout
            payload = {
                "property_id": first_property["id"],
                "guest_name": "TEST_OverlapBuyer",
                "guest_email": "overlapbuyer@example.com",
                "check_in": "2027-11-03",
                "check_out": "2027-11-08",
                "origin_url": "https://coastal-ops.preview.emergentagent.com",
            }
            r2 = requests.post(f"{API}/public/checkout", json=payload, timeout=15)
            assert r2.status_code == 409, f"expected 409, got {r2.status_code}: {r2.text}"

            # Quote with overlap should return available:false
            r3 = requests.get(
                f"{API}/public/quote",
                params={"property_id": first_property["id"], "check_in": "2027-11-03", "check_out": "2027-11-08"},
                timeout=15,
            )
            assert r3.status_code == 200
            assert r3.json()["available"] is False
        finally:
            # Cleanup: cancel the seeded overlap booking
            requests.patch(f"{API}/bookings/{booking_id}", json={"status": "cancelled"},
                           headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)


# ----------------------- Regression: existing manager APIs ----------------
class TestRegression:
    def test_manager_login(self, manager_token):
        assert isinstance(manager_token, str) and len(manager_token) > 10

    def test_manager_can_list_bookings(self, manager_token):
        r = requests.get(f"{API}/bookings", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_manager_can_list_ledger(self, manager_token):
        r = requests.get(f"{API}/accounting/ledger", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "ledgers" in body and "totals" in body

    def test_manager_can_list_housekeeping(self, manager_token):
        r = requests.get(f"{API}/housekeeping", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200

    def test_manager_can_list_guests(self, manager_token):
        r = requests.get(f"{API}/guests", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200

    def test_reports_analytics(self, manager_token):
        r = requests.get(f"{API}/reports/analytics", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200
        assert "kpis" in r.json()

    def test_owner_statement(self, manager_token):
        r = requests.get(f"{API}/owner/statement", headers={"Authorization": f"Bearer {manager_token}"}, timeout=15)
        assert r.status_code == 200

    def test_rates_update(self, manager_token, first_property):
        r = requests.patch(
            f"{API}/properties/{first_property['id']}/rates",
            json={"nightly": first_property["nightly"]},
            headers={"Authorization": f"Bearer {manager_token}"}, timeout=15,
        )
        assert r.status_code == 200
