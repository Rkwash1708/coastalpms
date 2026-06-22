# Coastline PMS — Product Requirements Document

## Original Problem Statement
Modern, cloud-based Property Management Software for small-to-medium Vacation Rental PMCs in the Southeast USA. Solves fragmentation of legacy PMS tools with a unified, fast, mobile-first platform addressing coastal operational challenges (salt-air corrosion, humidity HVAC strain, hurricane prep, owner communication overhead).

## Tech Stack
- Frontend: React 19 + React Router + Tailwind + Recharts + lucide-react (Stripe-meets-Airbnb design)
- Backend: FastAPI + Motor (MongoDB), JWT Bearer auth (role-based)
- AI: Emergent LLM key (OpenAI gpt-5.4 / gpt-5.4-mini) for inbox draft replies & translation

## User Personas
- Manager (Operations Director): full ops command center
- Housekeeper: mobile field app, photo Guest-Ready workflow, EN/ES toggle
- Maintenance Tech: mobile field app, before/after photos, storm checklists
- Owner: zero-phone-call portal (ROI, payout evidence, holds)

## Core Requirements (static)
1. Unified Operations & Field App — role dashboards, photo Guest-Ready, EN/ES localization
2. Coastal Maintenance Engine — predictive 60-day salt/HVAC tasks, Storm Mode dispatch
3. Zero-Phone-Call Owner Portal — financials, before/after evidence, owner holds
4. Unified Communications Hub — Airbnb/VRBO/SMS/Email inbox + AI-drafted replies
5. Automated Trust Accounting — split-ledger (owner / commission / cleaning / occupancy tax)

## Implemented (2026-06-20)
- JWT role-based auth + 7 seeded users; role-based routing (manager/owner/field)
- Manager Operations dashboard: stat cards, revenue chart, maintenance queue, Storm Mode activate/standdown
- Properties grid (6 seeded coastal/inland properties) + **Rates/Pricing editor** (weekday/weekend/min-nights/cleaning)
- Coastal Maintenance: predictive (Auto·60d) badges, storm tasks, filters, create-task modal
- Storm Mode: dispatches hurricane prep checklist tasks to field staff; coral UI accents
- Unified Inbox: multi-channel threads, real AI draft replies, send
- Trust Accounting: split-ledger summary + ledger table
- Owner Portal: revenue/payout/ROI cards, monthly payout chart, owner holds CRUD, before/after photo evidence, **Monthly Owner Statement (on-screen + printable PDF download)**
- Field App (mobile-first): housekeeping Guest-Ready photo upload, maintenance before/after + complete, EN/ES toggle
- **Reservations & Central Calendar**: multi-property availability grid, create booking (auto-bills split-ledger + auto-creates housekeeping turnover), booking/owner-hold overlap protection (409), upcoming arrivals
- **Guest CRM**: 14 seeded guests ranked by lifetime value, profile drawer with stay history + editable notes
- **Reporting & Analytics**: Occupancy %, ADR, RevPAR, Avg LOS, revenue-by-month bar, revenue-by-channel pie, property leaderboard
- Verified: iteration_1 26/26 + iteration_2 41/41 backend tests pass; all critical frontend flows pass

## Backlog (prioritized)
- P1: GPS tracking for storm-dispatched field staff (problem statement mentions it)
- P1: Channel manager — real Airbnb/VRBO/Booking.com sync (currently channel-tagged bookings)
- P2: Booking engine / direct-booking website + Stripe payments
- P2: Automated guest messaging templates & scheduled messages
- P2: Object storage for photos (currently base64 in Mongo) — move to S3 for scale
- P2: Reviews management; digital guidebook / check-in instructions
- P2: Split server.py into routers (bookings/guests/reports) as it grows
- P2: Guest upsert should match on email/phone, not name alone

## Next Tasks
- Confirm with user which P1 to tackle next (GPS field tracking vs. holds-calendar validation)
