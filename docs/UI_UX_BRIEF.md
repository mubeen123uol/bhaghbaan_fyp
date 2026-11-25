# Baghbaan AI — UI/UX Design Brief & Design System

---

## 1. Design Philosophy: "Urdu-First, Camera-First, Empathetic"

Baghbaan AI is engineered specifically for Pakistani gardeners of all digital literacy levels — from tech-savvy suburban plant collectors in Islamabad to traditional household gardeners (*malis*) and elders in Lahore and Karachi.

### Core UX Principles
1. **Camera-First Accessibility:** The primary entry point on mobile and web highlights photo diagnosis. One click opens the camera or file picker.
2. **Urdu-First Inclusivity:** Native Urdu text rendered with elegant Nastaliq typographic proportions, fully mirrored Right-to-Left (RTL) layouts, and accessible Roman Urdu and English options.
3. **Clarity Over Jargon:** Botanical and pathological terminology is translated into colloquial Pakistani terms (e.g., "سفید مکھی" for Whitefly, "پپھوندی" for Powdery Mildew, "پیلے پتے" for Chlorosis).
4. **Immediate Actionability:** Every diagnosis terminates with concrete, accessible steps (kitchen remedy vs. nursery pesticide) and direct links to hire a gardener or order supplies.

---

## 2. Color Palette & Theming

The visual theme evokes the lush greenery of the Indus fertile plains, terracotta nursery pots (*gamlas*), and fresh organic earth.

| Token | Hex Value | Color Name | Application |
|---|---|---|---|
| `--color-primary` | `#1b4332` | Emerald Forest | Primary buttons, headers, active navigation pills |
| `--color-primary-light` | `#2d6a4f` | Garden Green | Hover states, secondary action buttons, card headers |
| `--color-secondary` | `#52b788` | Sprout Green | Badges, success indicators, healthy plant status |
| `--color-surface` | `#f8f9fa` | Alabaster Mist | App background, subtle table stripes |
| `--color-card` | `#ffffff` | Pure White | Elevated cards, dialog sheets, modal containers |
| `--color-accent` | `#d4a373` | Terracotta / Clay | Warning badges, low confidence alerts, cart indicators |
| `--color-danger` | `#bc4749` | Rust Red | Disease severity tags, cancellation buttons, errors |
| `--color-text-main` | `#1f2937` | Charcoal Dark | Primary typography, body text, form labels |
| `--color-text-muted` | `#6b7280` | Stone Gray | Subtitles, timestamps, breadcrumbs, placeholder text |

---

## 3. Typography & RTL Engineering

### Font Stack
- **Urdu (RTL):** `'Noto Nastaliq Urdu'`, `'Gulzar'`, `'Jameel Noori Nastaleeq'`, `'Segoe UI'`, sans-serif.
  - Urdu text requires a larger line-height (`leading-loose` / `1.8 - 2.0`) and font-size boost ($+2\text{px}$ compared to Latin) to prevent ligature clipping.
- **English / Numerals (LTR):** `'Inter'`, `'Plus Jakarta Sans'`, system-ui, sans-serif.

### Bidirectional Layout Rules
- When the user selects Urdu:
  - Document element receives `<html lang="ur" dir="rtl">`.
  - Sidebar floats to the right; back-arrows point right ($\rightarrow$); icons flip horizontally where directional.
  - Numbers and dates retain standard formatting with Urdu numerals or standard digits as configured.
- When English is active:
  - Document element switches to `<html lang="en" dir="ltr">`.

---

## 4. Key Screen Wireframe Specifications

### 1. Home / Dashboard
- **Header:** Brand logo with leaf emblem ("باغبان"), language switcher pill (اردو / Roman Urdu / English), active notifications bell with unread badge, and profile avatar.
- **Hero Diagnostic Banner:** Large call-to-action card: *"بیمار پودے کی تصویر لیں یا اپلوڈ کریں"* (Take or upload a photo of your sick plant) with a camera icon.
- **Weather Widget:** Live card displaying user's current city temperature, weather condition (e.g. sunny, rain forecast), and intelligent garden advice badge (e.g. *"بارش متوقع ہے — آج پودوں کو پانی نہ دیں"*).
- **Quick Links Grid:**
  - 🌿 My Plants (میری نباتات)
  - 📅 Care Calendar (دیکھ بھال کا شیڈول)
  - 👨‍🌾 Hire a Gardener (مالی تلاش کریں)
  - 🛒 Nursery Supplies (پودوں کا بازار)
  - 💬 Community Chat (باغبانی برادری)

### 2. AI Plant Doctor (Diagnosis & Result)
- **Upload Stage:** Drag-and-drop zone, camera capture button, file size indicator ($< 5\text{MB}$ validation), and preview thumbnail.
- **Inference State:** Smooth pulsing leaf animation with bilingual status messages (*"تصویر کی جانچ ہو رہی ہے..."*).
- **Result Stage:**
  - Identified Species badge (Urdu name + Scientific Latin in italics).
  - Disease condition badge with color-coded severity.
  - **Confidence Gauge:** Visual progress bar with percentage. If $< 60\%$, shows cautionary alert: *"کم یقین — ماہر مالی سے مفت مشورہ لیں"* with an "Escalate" button.
  - **Treatment Tabs:**
    - Tab 1: Organic & Home Remedies (دیسی اور گھریلو علاج — e.g. نیم کا تیل، لکڑی کی راکھ).
    - Tab 2: Chemical & Commercial Treatment (کیمیکل ادویات) with prominent safety disclaimer icon.
  - **Action Toolbar:** "Save to My Plants", "Share to WhatsApp", "Buy Medicine in Market", "Consult Gardener".

### 3. Smart Care Calendar
- **Timeline View:** Day/Week calendar showing scheduled tasks (Watering 💧, Fertilizer 🧪, Pruning ✂️).
- **Weather-Aware Badges:** Tasks marked with warning pills if postponed due to expected rainfall.
- **Quick Completion:** Checkbox to mark tasks done, instantly logging completion date and updating next cycle.

### 4. Garden Services & Task Board
- **Role-Adaptive Layout:**
  - *Homeowner:* Overview of active gardens, current expenses vs. budget progress bar, task creation modal.
  - *Gardener:* Clean list of assigned tasks sorted by urgency, button to "Start Task" (`IN_PROGRESS`), and report submission sheet with camera attachment.
  - *Supervisor:* Inspection inbox with pending `SUBMITTED` reports, side-by-side photo comparison of before/after, "Approve" and "Return with Notes" buttons.

### 5. Marketplace-Lite & Checkout
- **Catalog Grid:** Clean responsive product cards with badge for nursery seller, stock availability tag, price in PKR (Rs.), and "Add to Cart" button.
- **Cart Sheet:** Slide-over cart displaying items, quantity steppers, subtotal, and delivery notes.
- **Checkout Modal:** Address confirmation, city selection, delivery phone number, and Cash on Delivery (COD) indicator.

### 6. Real-Time Chat & Rooms
- **Room List:** Segmented tabs for "Direct Messages", "My Gardens", and "Public Community Groups".
- **Chat Window:** Auto-scrolling message list with read receipts, avatar display, image upload support, and typing indicators.
