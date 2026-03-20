version: '3.9'

services:

  # ── PostgreSQL Database ──────────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: procurement_db
    environment:
      POSTGRES_USER:     user
      POSTGRES_PASSWORD: password
      POSTGRES_DB:       procurement
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
      - ./database/seed.sql:/docker-entrypoint-initdb.d/02_seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d procurement"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Python FastAPI Backend ───────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: procurement_backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL:      postgresql+asyncpg://user:password@postgres:5432/procurement
      SECRET_KEY:        ${SECRET_KEY:-changeme-in-production}
      TINYFISH_API_KEY:  ${TINYFISH_API_KEY}
      OPENAI_API_KEY:    ${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # ── React Frontend ───────────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: procurement_frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  postgres_data: