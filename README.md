# 🤖 ProcureAI — AI Procurement Agent

An autonomous procurement agent that navigates real supplier websites,
fills quote request forms, and returns ranked quotes — powered by
**TinyFish Web Agent API**, **OpenAI**, and **FastAPI + React**.

---

## How It Works

1. You describe what you need ("500 nitrile gloves size L")
2. AI parses your spec into structured data
3. Browser agents (TinyFish) navigate real supplier websites in parallel
4. Agents fill quote forms using your company profile
5. Quotes are ranked by price, delivery, and reliability
6. You get a clean comparison dashboard in seconds

---

## Tech Stack

| Layer       | Tech                          |
|-------------|-------------------------------|
| Frontend    | React 18 + Vite + TailwindCSS |
| Backend     | FastAPI (Python 3.12)         |
| Database    | PostgreSQL + SQLAlchemy       |
| AI Agents   | TinyFish Web Agent API        |
| LLM         | OpenAI GPT-4o                 |
| Auth        | JWT (python-jose)             |
| Containers  | Docker + Docker Compose       |

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo>
cd procurement-agent
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Add API Keys to .env

```
TINYFISH_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SECRET_KEY=any_long_random_string
```

### 3. Run with Docker (recommended)

```bash
docker-compose up --build
```

That's it. Open http://localhost:3000

---

## Local Dev (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

```bash
# Make sure PostgreSQL is running locally
# Create database: procurement
# Run: psql -U postgres -d procurement -f database/schema.sql
# Seed: psql -U postgres -d procurement -f database/seed.sql
```

---

## Project Structure

```
procurement-agent/
├── backend/
│   ├── main.py               # FastAPI entry
│   ├── config.py             # env vars
│   ├── routes/               # auth, procurement, quotes, suppliers
│   ├── agents/               # orchestrator, supplier, form, monitor
│   ├── services/             # tinyfish, llm, db, email
│   ├── models/               # SQLAlchemy ORM
│   └── engine/               # spec parser, matcher, comparator
├── frontend/
│   └── src/
│       ├── pages/            # Login, Dashboard, NewRequest, Quotes, Suppliers, Profile
│       ├── components/       # AgentStatusBar, QuoteCard, QuoteCompare, Navbar
│       └── services/         # api.js, useProcurement, useQuotes
├── database/
│   ├── schema.sql
│   └── seed.sql
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | /auth/register              | Create account                 |
| POST   | /auth/login                 | Get JWT token                  |
| GET    | /auth/me                    | Get current user profile       |
| PUT    | /auth/profile               | Update company profile         |
| POST   | /procurement/run            | Submit new procurement request |
| GET    | /procurement/{id}           | Poll job status + agent log    |
| GET    | /procurement/               | List all requests              |
| GET    | /quotes/{procurement_id}    | Get ranked quotes              |
| GET    | /suppliers/                 | List suppliers                 |
| POST   | /suppliers/                 | Add custom supplier            |
| DELETE | /suppliers/{id}             | Remove supplier                |

---

## Built for TinyFish Hackathon 2026

