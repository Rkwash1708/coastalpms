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
- Properties grid (6 seeded coastal/inland properties)
- Coastal Maintenance: predictive (Auto·60d) badges, storm tasks, filters, create-task modal
- Storm Mode: dispatches hurricane prep checklist tasks to field staff; coral UI accents
- Unified Inbox: multi-channel threads, real AI draft replies, send
- Trust Accounting: split-ledger summary + 106-row ledger table
- Owner Portal: revenue/payout/ROI cards, monthly payout chart, owner holds CRUD, before/after photo evidence
- Field App (mobile-first): housekeeping Guest-Ready photo upload, maintenance before/after + complete, EN/ES toggle
- Verified: 26/26 backend tests pass; all critical frontend flows pass (testing iteration_1)

## Backlog (prioritized)
- P1: GPS tracking for storm-dispatched field staff (problem statement mentions it)
- P1: Owner holds should block/validate against booking calendar
- P2: AI reply rate limiting / debounce
- P2: Object storage for photos (currently base64 in Mongo) — move to S3 for scale
- P2: Real channel integrations (Airbnb/VRBO/Twilio SMS) — currently seeded threads
- P2: Bulk-cancel storm tasks on stand-down via manager UI

## Next Tasks
- Confirm with user which P1 to tackle next (GPS field tracking vs. holds-calendar validation)
