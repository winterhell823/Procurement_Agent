-- AI Procurement Agent — PostgreSQL Schema
-- Run this if you prefer raw SQL over SQLAlchemy auto-create

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    hashed_password   VARCHAR(255) NOT NULL,
    full_name         VARCHAR(255),
    company_name      VARCHAR(255),
    company_address   TEXT,
    company_phone     VARCHAR(50),
    contact_person    VARCHAR(255),
    payment_terms     VARCHAR(100) DEFAULT 'Net 30',
    gst_number        VARCHAR(100),
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- ── Suppliers ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    website_url       VARCHAR(500) NOT NULL,
    category          VARCHAR(255),
    categories        JSONB DEFAULT '[]',
    quote_form_url    VARCHAR(500),
    login_required    BOOLEAN DEFAULT FALSE,
    navigation_hint   TEXT,
    is_active         BOOLEAN DEFAULT TRUE,
    is_global         BOOLEAN DEFAULT FALSE,
    reliability_score VARCHAR(10),
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- ── Procurement Requests ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS procurement_requests (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_description   TEXT NOT NULL,
    parsed_spec       JSONB,
    quantity          INTEGER,
    budget            VARCHAR(100),
    deadline          VARCHAR(100),
    status            VARCHAR(50) DEFAULT 'pending',
    status_message    TEXT,
    agent_log         JSONB DEFAULT '[]',
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- ── Quotes ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS quotes (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    procurement_request_id  UUID NOT NULL REFERENCES procurement_requests(id) ON DELETE CASCADE,
    supplier_id             UUID REFERENCES suppliers(id),
    supplier_name           VARCHAR(255) NOT NULL,
    supplier_url            VARCHAR(500),
    unit_price              NUMERIC(12,2),
    total_price             NUMERIC(12,2),
    currency                VARCHAR(10) DEFAULT 'INR',
    delivery_days           VARCHAR(100),
    minimum_order_qty       VARCHAR(100),
    payment_terms           VARCHAR(100),
    additional_notes        TEXT,
    raw_extracted_data      JSONB,
    score                   NUMERIC(5,2),
    is_recommended          BOOLEAN DEFAULT FALSE,
    status                  VARCHAR(50) DEFAULT 'fetching',
    fetched_at              TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_procurement_user    ON procurement_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_procurement  ON quotes(procurement_request_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_category  ON suppliers(category);
CREATE INDEX IF NOT EXISTS idx_suppliers_global    ON suppliers(is_global);