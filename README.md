# 🌿 Plant Disease Advisor

An AI-powered agricultural advisory platform that diagnoses 38 crop diseases from leaf photographs, provides plain-language explanations with offline fallback, facilitates interactive follow-up chat, and offers ICAR-aligned chemical/biological product sourcing guidance.

---

## 🚀 Key Features

* **38-Class Disease Classifier:** MobileNetV2 model converted to TensorFlow Lite with 8-bit dynamic-range quantization (2.57 MB, mean CPU inference latency: ~20.5 ms).
* **Confidence-Based Rejection:** Low-confidence predictions (< 0.70) are rejected with an "uncertain" warning, protecting farmers from misleading results.
* **Conversational AI Diagnosis Feed:** Diagnosis results render as a conversational chat thread (leaf photo upload bubble followed by structured AI diagnosis response).
* **Two-Tier Safe Advisory & Sourcing Architecture:**
  1. *Core Diagnosis Explanation (`/predict`):* Returns symptoms, causes, and cultural prevention. The LLM prompt strictly prohibits prescribing pesticide brand names or specific dosages.
  2. *Curated Support Directory (`/support`):* Curated knowledge base (`support_info.json`) providing broad active-ingredient categories (e.g. copper-based protectants, Mancozeb, bio-control *Trichoderma* formulations) referenced from **Indian Council of Agricultural Research (ICAR)** and State Agricultural University (SAU) package of practices. **Strictly zero dosages** are provided, with an explicit mandatory agricultural extension officer sign-off disclaimer on every card.
* **Multi-Turn Follow-Up AI Chat (`/chat`):** Authenticated users can ask follow-up questions tied to their diagnosis record. Responses are contextualized to the specific disease.
* **Verified Sourcing Directory:** Direct links to certified input suppliers (BigHaat, AgroStar, IFFCO eBazar, Krishi Vigyan Kendra, and licensed local dealers).
* **Tenant-Isolated Multi-User Auth:** Bcrypt password hashing, JWT bearer tokens, and per-user row-level data isolation.
* **Zero-Build Lightweight UI:** Responsive single-page web app built with vanilla HTML/CSS/JS and green-to-teal gradients — no npm, webpack, or React required.

---

## 📡 RESTful API Reference

All protected endpoints require an `Authorization: Bearer <token>` header. Interactive OpenAPI documentation is available at `/docs` (Swagger UI).

| Method | Endpoint | Auth Required | Description |
|---|---|:---:|---|
| `GET` | `/health` | No | Liveness health probe (`{"status": "ok"}`) |
| `GET` | `/classes` | No | Lists all 38 supported plant disease classes |
| `POST` | `/auth/register` | No | Register a new user account |
| `POST` | `/auth/login` | No | Authenticate user credentials and issue JWT token |
| `GET` | `/auth/me` | Yes | Retrieve the currently logged-in user profile |
| `POST` | `/predict` | Yes | Upload leaf image (JPEG/PNG, max 5 MB) for classification & explanation |
| `GET` | `/predictions` | Yes | List past diagnosis records (supports `skip`, `limit`, `disease` filtering) |
| `GET` | `/predictions/{id}` | Yes | Fetch details and explanation for a specific diagnosis |
| `PUT` | `/predictions/{id}` | Yes | Update diagnosis note or correct disease class label |
| `DELETE` | `/predictions/{id}` | Yes | Delete a saved diagnosis record (cascades to chat messages) |
| `POST` | `/predictions/{id}/chat` | Yes | Send a follow-up question to the AI assistant about this diagnosis |
| `GET` | `/predictions/{id}/chat` | Yes | Retrieve the full multi-turn chat history for a diagnosis |
| `GET` | `/predictions/{id}/support` | Yes | Retrieve ICAR-aligned chemical active classes, certified stores, and disclaimer |

---

## 🛡️ Agricultural Safety Policy

> **⚠️ Important Safety Principle:** Injudicious or incorrect chemical application can destroy a farmer's crop, cause chemical burn, or leave harmful residue.

To guarantee high safety and academic rigor:
1. **Zero Chemical Dosages:** Neither the LLM nor the support directory ever emits dosages (e.g., "g/L" or "ml/ha").
2. **Generic Active Ingredients Only:** We list scientific chemical classes and bio-agents (e.g. *Copper Oxychloride*, *Mancozeb*, *Trichoderma viride*), avoiding unverified commercial trade formulations.
3. **Mandatory Officer Consultation:** Every advisory explicitly instructs farmers: *"Always consult your local agricultural extension officer or Krishi Vigyan Kendra (KVK) specialist to confirm product suitability, stage-specific timing, and safe application rates before purchase."*

---

## 🗄️ Database Schema

The database uses SQLite (SQLAlchemy ORM) with foreign key enforcement and cascade deletion:

```
users
  ├── id (PK, Integer)
  ├── username (Unique, String)
  ├── password_hash (String)
  └── created_at (DateTime, UTC)
        │
        └──< predictions
               ├── id (PK, Integer)
               ├── user_id (FK -> users.id)
               ├── disease (String)
               ├── confidence (Float)
               ├── status (String: "ok" | "uncertain")
               ├── explanation_json (Text)
               ├── note (Text)
               ├── created_at (DateTime, UTC)
                     │
                     └──< chat_messages
                            ├── id (PK, Integer)
                            ├── record_id (FK -> predictions.id)
                            ├── role (String: "user" | "assistant")
                            ├── content (Text)
                            └── created_at (DateTime, UTC)
```

---

## 🧪 Testing & Verification

The suite includes **13 automated tests** covering authentication, input sanitization, multi-tenant isolation, CRUD, where-to-buy support data, and multi-turn chat persistence. Tests run against an isolated SQLite test database with external LLM calls disabled (`USE_LLM=false`).

Run tests using pytest:

```bash
pytest tests/testapi.py
```

Result:
```
======================= 13 passed, 1 warning in 10.11s ========================
```

---

## 💻 Running the Application

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.13)
* Virtual environment (`venv`)

### 2. Environment Configuration
Create or edit `.env`:
```env
JWT_SECRET=your_jwt_secret_key_here
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_groq_api_key_here
USE_LLM=true
LLM_TIMEOUT=12
```

### 3. Run the Backend API
```bash
uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
```

### 4. Open the Web Application
Open `consumer/index.html` in any modern web browser or serve it with any static web server.
