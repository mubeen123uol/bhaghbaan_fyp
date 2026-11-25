# Baghbaan AI — Product Requirements Document (PRD)
**Project Title:** Baghbaan AI: An Urdu-First, AI-Powered Smart Garden Companion for Pakistan  
**Academic Affiliation:** BS Software Engineering, Department of Software Engineering, Faculty of CS & IT, The Superior University, Lahore  
**Supervision:** Ma'am Aimen Fatima (Lecturer) | Dr. Muhammad Aqeel (HoD)  
**FYP ID:** BSSE-FYP-F25-001  

---

## 1. Executive Summary & Vision

Pakistani home gardening has grown dramatically with urbanisation, food-security awareness, and social media interest. However, local gardeners face a severe digital divide: existing gardening platforms (Plantix, PictureThis, Planta) are English-first, Western-centric in plant knowledge and climate data, locked behind costly subscriptions, and detached from practical local ecosystems. When a Pakistani gardener diagnoses an infected Neem tree, Guava bush, Mint patch, or Chameli in Lahore's scorching June heat, existing apps provide irrelevant advice and offer no direct bridge to local treatment, local verified gardeners (*malis*), or nursery supplies.

**Baghbaan AI** bridges this gap as an Urdu-first, intelligent smart garden companion. It unifies:
1. **AI Plant Doctor:** Multimodal plant disease diagnosis combining Google Gemini Vision and Plant.id with an offline knowledge base fallback, outputting bilingual actionable advice (Urdu / Roman Urdu / English) with confidence scoring and expert escalation.
2. **Smart Care & Community:** Hyper-local, weather-aware care scheduling (using live Open-Meteo data), plant health timelines, and interest/location-based gardening groups with real-time chat.
3. **Garden Services & Marketplace-Lite:** Proximity-based discovery and booking of verified gardeners with a strict 5-state task lifecycle, alongside a cash-on-delivery (COD) gardening supplies marketplace with admin verification and automated commission tracking.

---

## 2. Target User Classes & Personas

| User Role | Description | Core Capabilities & Permissions |
|---|---|---|
| **Homeowner (Primary User)** | Urban/suburban home gardener managing indoor and outdoor plants | Upload plant photos for diagnosis, view Urdu care advice, maintain "My Plants" inventory, track care calendars, create gardens, hire gardeners, buy marketplace products via COD, join community chats. |
| **Gardener (*Mali*)** | Professional or semi-professional gardening worker | Receive garden invitations, view assigned tasks, transition task status (In Progress, Submitted), submit work reports with photo evidence, communicate in garden team chat. |
| **Supervisor** | Senior verified horticulturist or garden contractor | Oversee gardens, assign tasks to gardeners, inspect submitted task reports, approve or request revisions, record garden expenditures against budget. |
| **Seller** | Local nursery, seed supplier, or fertilizer vendor | Apply for seller status, list plants/tools/fertilizers with photos and pricing upon admin approval, manage order fulfillment. |
| **Administrator** | System admin (Web only) | Verify gardeners and sellers, approve marketplace listings, configure AI thresholds and API keys, manage plant/disease knowledge bases, moderate chat rooms and audit platform logs. |

---

## 3. Functional Requirements (FR)

### Module 1: Accounts, Profiles & RBAC
- **FR-A1: Unified Registration:** Support sign up with email/phone, secure password, and primary role selection (*Homeowner*, *Gardener*, *Supervisor*).
- **FR-A2: Dual Authentication:** Web client authenticates via secure Django sessions with CSRF protection; mobile/API clients authenticate via JSON Web Tokens (JWT) using `rest_framework_simplejwt`.
- **FR-A3: Localized User Profile:** Store user profile details including display name, phone, city (e.g. Lahore, Karachi, Islamabad, Rawalpindi, Faisalabad, Multan), GPS coordinates (latitude/longitude), and language preference (*Urdu RTL*, *Roman Urdu*, *English*).
- **FR-A4: Role-Based Access Control (RBAC):** Strict permissions enforced on every Django template view and DRF API endpoint (`IsOwner`, `IsGardenerMember`, `IsSupervisor`, `IsAdminUser`).
- **FR-A5: Seller Application Flow:** Registered users can apply to become verified sellers by submitting CNIC/shop verification details for Admin approval.
- **FR-A6: Device Token Management:** Store and refresh Firebase Cloud Messaging (FCM) device tokens for push notifications.

### Module 2: AI Plant Doctor
- **FR-D1: Photo Upload & Ingestion:** Upload or capture leaf/plant photos in JPEG/PNG formats (enforced max 5.0 MB).
- **FR-D2: Non-Plant Guardrail:** Validate if the uploaded image is genuinely a plant before invoking expensive inference models. Reject non-plant images (e.g., furniture, pets, vehicles) with a polite bilingual message.
- **FR-D3: Multi-Provider Disease & Species Identification:** Query Plant.id and Google Gemini Vision to detect plant species and identify diseases with associated probabilities.
- **FR-D4: Contextual Treatment Advice Generation:** Generate organic (home/natural remedies) and chemical treatments in Urdu, Roman Urdu, or English using Gemini, taking into account local climate, city, and current season.
- **FR-D5: Confidence Score & Explainability:** Display an aggregate confidence percentage, key visible symptoms matched, and standard agricultural safety disclaimers.
- **FR-D6: Low-Confidence Escalation:** When confidence falls below the admin-configured threshold (default 60%), prompt the user to escalate to a verified gardener or community forum.
- **FR-D7: Multi-Tier Fallback Chain:**
  1. *Primary:* Gemini + Plant.id consensus.
  2. *Secondary (Plant.id down):* Gemini Vision standalone diagnosis.
  3. *Tertiary (Gemini advice down):* Curated knowledge base treatment advice for detected disease.
  4. *Offline/Quota Exhausted:* Searchable offline plant encyclopedia with pre-written Urdu treatment templates.
- **FR-D8: Diagnosis History:** Persist user diagnoses with timestamp, uploaded photo, identified condition, treatment recommendations, and confidence score.
- **FR-D9: Domain-Restricted Urdu Voice/Text Chatbot:** Interactive gardening assistant answering care questions in Urdu/English, strictly restricted to botanical and gardening domains.

### Module 3: Smart Care & Community
- **FR-C1: Pakistani Plant Encyclopedia:** Searchable catalog of 40–60 indigenous and commonly cultivated Pakistani plants (e.g., Neem, Moringa, Money Plant, Chameli, Guava, Rose, Tomato, Mint, Coriander) with botanical names, Urdu names, and seasonal requirements.
- **FR-C2: "My Plants" Digital Garden:** Users can register owned plants with custom nicknames, acquisition date, indoor/outdoor flag, garden association, and photos.
- **FR-C3: Weather-Aware Care Calendar:** Automatically schedule watering, fertilizing, and pruning intervals. Adjust schedules using real-time Open-Meteo weather forecasts:
  - Postpone watering if $\ge 5\text{ mm}$ rain is forecast within 24 hours.
  - Shorten watering intervals during extreme heat ($\ge 38^\circ\text{C}$).
  - Inject frost warnings for sensitive outdoor plants during winter cold snaps.
- **FR-C4: Multi-Channel Reminder Dispatcher:** Dispatch due reminders through in-app notifications, push notifications, and emails via an idempotent 15-minute background worker.
- **FR-C5: Plant Health Timeline:** Track historical photos and milestone notes for individual plants to visualize recovery and growth.
- **FR-C6: Social Sharing:** Quick-share plant diagnoses and care guides to WhatsApp with formatted Urdu text and link previews.
- **FR-M1: Gardening Groups & Proximity Search:** Discover and join community groups based on geographic proximity (Haversine formula) and topic interests (e.g., Kitchen Gardening Lahore, Rose Enthusiasts).
- **FR-M2: Real-Time Chat Rooms:** Support Direct Chat (buyer-seller, homeowner-gardener), Garden Team Chat (restricted to garden members), and Community Chat with photo messaging.
- **FR-M3: Admin Moderation:** Capability for supervisors and administrators to flag, hide, or delete abusive messages and ban offending users.

### Module 4: Garden Services & Marketplace-Lite
- **FR-S1: Garden Profiles & Budget Management:** Homeowners can create multiple garden spaces, set total budgets, and monitor ongoing expenses.
- **FR-S2: Gardener Proximity Search:** Search verified gardeners and supervisors by city and radial distance.
- **FR-S3: Team Delegation:** Assign registered gardeners and supervisors to a garden.
- **FR-S4: 5-State Task Lifecycle:** Strictly enforce valid task transitions:
  $$\text{Created} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Submitted} \longrightarrow \text{Approved}$$
  *(or return from Submitted to In Progress if report is rejected)*.
- **FR-S5: Task Reporting:** Gardeners submit completion reports with photo proof and work notes. Homeowners/supervisors review and approve.
- **FR-S6: Expense Ledger:** Track purchases (seeds, tools, fertilizers, labor wages) charged against garden budgets.
- **FR-K1: Seller Verification Workflow:** Admins review and verify seller profiles before products can go live.
- **FR-K2: Product Catalog:** Verified sellers list gardening products with category, price, stock quantity, and gallery images. Listings require Admin approval.
- **FR-K3: Cart & Cash-On-Delivery (COD):** Homeowners browse approved products, add to cart, and check out with Cash-on-Delivery.
- **FR-K4: Order Status Tracking:** Track orders through: `Placed` $\rightarrow$ `Confirmed` $\rightarrow$ `Shipped` $\rightarrow$ `Delivered` $\rightarrow$ `Cancelled`.
- **FR-K5: Commission Ledger:** Apply platform commission (admin configurable flat rate or percentage) on each delivered order and generate commission settlement reports.

### Module 5: Administration & Maintenance
- **FR-X1: Django Admin Suite:** Comprehensive administrative interface to manage users, plants, diseases, orders, and content moderation.
- **FR-X2: AI Engine Controls:** Runtime administration settings for AI provider order, confidence thresholds, and API quota budgets.
- **FR-X3: Bulk Knowledge Base Importer:** CSV/JSON import utility for bulk loading Pakistani plant profiles, seasonal care parameters, and disease treatment protocols.

---

## 4. Non-Functional Requirements (NFR)

- **NFR-P1 (Performance):** Standard web page responses and REST API endpoints respond within $< 1000\text{ ms}$ at 95th percentile under normal loads.
- **NFR-R1 (Reliability):** AI fallback architecture guarantees useful botanical feedback even if external vision APIs suffer partial or complete outage.
- **NFR-S1 (Security):** Passwords hashed via PBKDF2/Argon2; CSRF enforced on all web forms; JWT tokens rotated; file uploads strictly validated for MIME type, file extension, and max size (5 MB) with sanitized storage filenames.
- **NFR-U1 (Usability & Localization):** Native Urdu typography using Nastaliq/Gulzar web fonts, fully integrated Right-To-Left (RTL) stylesheets, and English/Urdu one-click toggle. SUS (System Usability Scale) target $\ge 70$.
- **NFR-M1 (Maintainability):** Clear service-layer separation isolating business logic from views and serializers, ensuring 100% logic parity between Django Templates web client and DRF mobile clients.
