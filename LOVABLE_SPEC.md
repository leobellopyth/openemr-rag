# OpenEMR Clinical Decision Support - Lovable Spec

## Project Overview

**Project Name:** OpenEMR CDS  
**Type:** Healthcare AI Web Application  
**Core Functionality:** Clinical decision support system that connects to OpenEMR via a local backend API, providing AI-powered patient analysis and clinical insights.  
**Target Users:** Healthcare providers (RNs, MDs) and health informatics students

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Lovable Frontend (React/Next.js)                       │
│ https://openemr-cds.lovable.dev                       │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Local Backend Server (Port 3002)                       │
│ http://localhost:3002                                  │
│ - Flask REST API                                       │
│ - RAG pipeline (LangChain + Ollama)                   │
│ - SSH tunnel to OpenEMR                                │
└─────────────────────────────────────────────────────────┘
```

**IMPORTANT:** The frontend MUST connect to `http://localhost:3002`. For Lovable cloud deployment to work with a local backend, use ngrok or cloudflare tunnel to expose port 3002 publicly.

## Design Language

### Color Palette
- **Primary:** #0066CC (Medical Blue)
- **Secondary:** #00A878 (Health Green)
- **Accent:** #FF6B35 (Alert Orange)
- **Background:** #F8FAFC (Light Gray)
- **Surface:** #FFFFFF (White)
- **Text Primary:** #1E293B (Dark Slate)
- **Text Secondary:** #64748B (Slate Gray)
- **Error/Alert:** #DC2626 (Red)
- **Warning:** #F59E0B (Amber)
- **Success:** #10B981 (Emerald)

### Typography
- **Font Family:** Inter (Google Fonts)
- **Headings:** 600-700 weight
- **Body:** 400-500 weight
- **Monospace:** For clinical codes (ICD-10)

### Spacing
- Base unit: 4px
- Consistent padding: 16px, 24px, 32px
- Card spacing: 16px gap

## Layout Structure

### Page 1: Main Dashboard (Single Page App)

```
┌─────────────────────────────────────────────────────────┐
│ Header                                                  │
│ ┌─────────────────┐  ┌──────────────────────────────┐  │
│ │ 🏥 OpenEMR CDS │  │ [Demo] [Live] ● Connection    │  │
│ └─────────────────┘  └──────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────┐  ┌───────────────────────┐  │
│ │ Patient Panel          │  │ Clinical Chat          │  │
│ │                        │  │                        │  │
│ │ Patient ID: [____]    │  │ ┌───────────────────┐ │  │
│ │ [Search]               │  │ │ AI Response Area   │ │  │
│ │                        │  │ │                    │ │  │
│ │ ┌──────────────────┐  │  │ │                    │ │  │
│ │ │ Patient Card      │  │  │ └───────────────────┘ │  │
│ │ │ Name: Sarah J.   │  │  │                        │  │
│ │ │ DOB: 1978-05-15  │  │  │ [Ask clinical question] │  │
│ │ │ Conditions: 2    │  │  │                        │  │
│ │ │ Meds: 2          │  │  └───────────────────────┘  │
│ │ │ Allergies: 1      │  │                             │
│ │ └──────────────────┘  │  ┌───────────────────────┐  │
│ │                        │  │ Quick Analysis        │  │
│ │ Vitals Summary        │  │ ┌─────┐┌─────┐┌────┐ │  │
│ │ BP: 138/88 HR: 78    │  │ │Vitals││Meds ││Risk│ │  │
│ │ SpO2: 97%            │  │ └─────┘└─────┘└────┘ │  │
│ └───────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Responsive Behavior
- Desktop: Two-column layout (Patient | Chat)
- Tablet: Stacked panels
- Mobile: Tab-based navigation

## Features & Interactions

### 1. Mode Toggle (Demo/Live)
- **Default:** Demo mode on load
- **Demo:** Uses sample patient data built-in
- **Live:** Connects to local backend (shows "Connecting..." state)
- **Visual:** Pill toggle with active state indicator

### 2. Patient Search
- **Input:** Text field for patient ID
- **Button:** "Search" or press Enter
- **Demo Mode:** Shows demo patients (1, 2, 3)
- **Live Mode:** Fetches from OpenEMR via backend
- **Error:** "Patient not found" toast notification
- **Loading:** Spinner during fetch

### 3. Patient Card (Display Only)
- **Fields shown:**
  - Name
  - DOB / Age (calculated)
  - Gender
  - Conditions (list)
  - Active Medications (list)
  - Allergies (list with reaction)
- **Empty state:** "Select a patient to view details"

### 4. Vitals Display
- Compact table/list format
- Most recent values highlighted
- Color coding:
  - Green: Normal
  - Amber: Borderline
  - Red: Critical

### 5. Clinical Chat
- **Input:** Multi-line text area
- **Placeholder:** "Ask a clinical question..."
- **Submit:** Button or Ctrl+Enter
- **Response:** Displayed in scrollable area
- **Loading:** "Analyzing..." with spinner
- **Clear:** Button to reset chat

### 6. Quick Analysis Buttons
- **Vitals Review:** Analyze vital signs
- **Medication Review:** Check medications
- **Risk Assessment:** Identify clinical risks
- **Care Gaps:** Preventive care gaps
- **Behavior:** Each opens modal or appends to chat
- **Loading state:** Button shows spinner during analysis

### 7. Connection Status Indicator
- **Demo mode:** Gray dot + "Demo Mode"
- **Connecting:** Yellow dot + "Connecting..."
- **Connected:** Green dot + "Live - OpenEMR Connected"
- **Error:** Red dot + "Connection Failed"

## Component Inventory

### Header
- Logo/Title left-aligned
- Mode toggle center
- Connection status right
- **States:** Default

### Mode Toggle
- Pill-shaped toggle
- Two options: Demo | Live
- **States:** Default, Hover, Active

### Patient Search Input
- Text input with icon
- **States:** Empty, Filled, Focused, Error, Loading

### Patient Card
- White card with subtle shadow
- Sections for demographics, conditions, meds, allergies
- **States:** Empty, Loading, Populated, Error

### Vitals Table
- Striped rows
- Header row bold
- **States:** Empty, Loading, Populated

### Chat Message
- User messages: Right-aligned, blue background
- AI responses: Left-aligned, gray background
- **States:** User, AI, Loading

### Analysis Button
- Icon + Label
- Outlined style
- **States:** Default, Hover, Active, Loading, Disabled

### Toast Notification
- Slides in from top-right
- Auto-dismisses after 4 seconds
- **Types:** Success (green), Error (red), Info (blue)

## Technical Approach

### Frontend (Lovable)
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS
- **State:** React hooks (useState, useEffect)
- **HTTP:** fetch API or axios
- **Icons:** Lucide React

### Backend (Local Python Server)
- **Framework:** Flask
- **Port:** 3002
- **CORS:** Enabled for localhost
- **SSH Tunnel:** Auto-start on /connect

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /connect | Start SSH tunnel |
| POST | /disconnect | Stop SSH tunnel |
| GET | /patient/:id | Get patient by ID |
| GET | /patients | List patients (demo) |
| POST | /query | Clinical query |
| POST | /analyze/:type | Run specific analysis |

### API Request/Response Examples

**GET /patient/1?mode=demo**
```json
{
  "id": "1",
  "name": "Sarah Johnson",
  "birthDate": "1978-05-15",
  "gender": "female",
  "conditions": [...],
  "medications": [...],
  "allergies": [...],
  "vitals": [...]
}
```

**POST /query**
```json
{
  "question": "Review this patient's vitals",
  "patient_id": "1",
  "mode": "demo"
}
```
Response:
```json
{
  "answer": "The patient's vitals show..."
}
```

**POST /analyze/vitals**
```json
{
  "patient_id": "1",
  "mode": "demo"
}
```
Response:
```json
{
  "type": "vitals",
  "patient_id": "1",
  "analysis": "BP is slightly elevated..."
}
```

## Demo Patient Data

| ID | Name | Key Conditions | Notes |
|----|------|----------------|-------|
| 1 | Sarah Johnson | T2DM, HTN | On Metformin, Lisinopril |
| 2 | Michael Chen | COPD, CHF | On Albuterol, Furosemide |
| 3 | Emily Rodriguez | Asthma | On Fluticasone |

## Non-Functional Requirements

- **Performance:** Response within 5 seconds for queries
- **Accessibility:** WCAG 2.1 AA compliance
- **Security:** No PHI stored client-side
- **Privacy:** Clear disclaimer about demo mode
