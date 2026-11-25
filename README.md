# باغبان اے آئی (Baghbaan AI)
### An Urdu-First, AI-Powered Smart Garden Companion for Pakistan

**Final Year Project (Session 2022–2026)**  
**Department of Software Engineering, Faculty of CS & IT, The Superior University, Lahore**  
**Supervisor:** Ma'am Aimen Fatima (Lecturer) | **Head of Department:** Dr. Muhammad Aqeel  
**FYP ID:** BSSE-FYP-F25-001  

---

## 📌 Project Overview

**Baghbaan AI** is an intelligent, Urdu-first smart garden companion tailored specifically for Pakistani home gardeners, local flora, and regional weather conditions. It provides a consolidated Django backend serving both an interactive web application (Django Templates + Tailwind CSS + HTMX) and a native Android application via Django REST Framework (DRF) JSON APIs and Django Channels WebSockets.

### Key Pillars
1. **AI Plant Doctor:** Multimodal plant disease diagnosis using Google Gemini Vision and Plant.id with an offline botanical knowledge base fallback. Delivers bilingual advice (Urdu / Roman Urdu / English) with confidence scores and expert gardener escalation.
2. **Smart Care & Community:** Weather-aware care calendars dynamically adjusted via live Open-Meteo weather forecasts (e.g., auto-postponing watering on $\ge 5\text{ mm}$ rain), plant health timelines, and interest-based groups with real-time chat.
3. **Garden Services & Marketplace-Lite:** Proximity-based gardener and supervisor discovery, a strict 5-state task lifecycle (`CREATED` $\rightarrow$ `ASSIGNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `SUBMITTED` $\rightarrow$ `APPROVED`), and a Cash-on-Delivery (COD) gardening supplies marketplace with admin-recorded commissions.

---

## 🏗️ Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend Framework** | Django 6.0+ | Robust ORM, built-in admin, security, i18n support |
| **REST APIs** | Django REST Framework (DRF) 3.18+ | Standardized JSON serialization, throttling, permissions |
| **API Auth & Docs** | SimpleJWT + drf-spectacular | Stateless token authentication & auto-generated OpenAPI 3.0 / Swagger |
| **Database** | SQLite 3 in WAL Mode | Concurrent reads/writes, zero-configuration ACID persistence |
| **Frontend** | Django Template Engine | Server-rendered SSR, zero client bundle weight, maximum responsiveness |
| **Styling & RTL** | Tailwind CSS + Google Fonts | Clean responsive layout with native Nastaliq Urdu Right-to-Left (RTL) |
| **Real-time Chat** | Django Channels 4.3+ & Daphne | WebSockets for live group, team, and direct messaging |
| **AI Vision & NLP** | Google Gemini Vision & Plant.id API | Accurate botanical leaf diagnosis and localized Urdu recommendations |
| **Weather Engine** | Open-Meteo REST API | Real-time precipitation and temperature forecast integration |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.12+ (or Python 3.14)
- Virtual environment (recommended)

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure your API keys (optional for local fallback):
```env
SECRET_KEY=baghbaan-ai-secure-django-secret-key-2026-fyp
DEBUG=True
GEMINI_API_KEY=your_gemini_api_key_here
PLANT_ID_API_KEY=your_plant_id_api_key_here
DEFAULT_CITY=Lahore
DEFAULT_LATITUDE=31.5204
DEFAULT_LONGITUDE=74.3587
```

### 3. Database Migration & Seeding
Run migrations and populate the database with 40+ Pakistani plants, diseases, treatments, sample users, gardens, and marketplace products:
```bash
python manage.py migrate
python manage.py seed_db
```

### 4. Start the Application Server
Run the standard development server:
```bash
python manage.py runserver
```
Or run with Daphne ASGI for WebSocket support:
```bash
daphne -b 127.0.0.1 -p 8000 baghbaan.asgi:application
```

Visit in your browser: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🔑 Pre-Seeded Evaluation Accounts

The database seeder configures accounts across all platform roles. On the login screen, convenient one-click fill buttons are provided for instant evaluation:

| Role | Username | Password | Purpose & Capabilities |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Django Admin portal, seller verification, AI settings |
| **Homeowner** | `ahmed` | `password123` | AI diagnosis, digital garden, care calendar, task creator |
| **Gardener** | `ali_mali` | `password123` | Task execution, report submission with photo proof |
| **Supervisor** | `tariq_supervisor` | `password123` | Task inspection, report approvals and revisions |
| **Seller** | `bilal_nursery` | `password123` | Nursery seller portal, product listings, COD orders |

---

## 🧪 Automated Testing

Execute the test suite covering task state machines, weather care rules, COD checkout, and REST APIs:
```bash
python manage.py test
```

---

## ⚙️ Background Management Commands

- **Dispatch Care Reminders & Sync Weather (every 15 mins):**
  ```bash
  python manage.py send_reminders
  ```
- **Bulk Import Plant Encyclopedia from CSV:**
  ```bash
  python manage.py import_plants_csv <path_to_csv>
  ```
- **Export OpenAPI 3.0 Schema for Mobile Team:**
  ```bash
  python manage.py spectacular --file schema.yml
  ```

---

## 📖 Project Documentation

Complete software engineering documentation artifacts are located in the `docs/` folder:
- [PRD.md](file:///d:/bhagbaan%20fyp/docs/PRD.md): Product Requirements Document
- [TRD.md](file:///d:/bhagbaan%20fyp/docs/TRD.md): Technical Requirements & System Architecture
- [APP_FLOW.md](file:///d:/bhagbaan%20fyp/docs/APP_FLOW.md): Application Flows, Sequence & State Diagrams
- [UI_UX_BRIEF.md](file:///d:/bhagbaan%20fyp/docs/UI_UX_BRIEF.md): UI/UX Design System, Typography & RTL Guidelines
- [BACKEND_SCHEMA.md](file:///d:/bhagbaan%20fyp/docs/BACKEND_SCHEMA.md): Complete Relational Schema & ORM Data Models
- [IMPLEMENTATION_PLAN.md](file:///d:/bhagbaan%20fyp/docs/IMPLEMENTATION_PLAN.md): 10-Phase Milestone & Implementation Roadmap
