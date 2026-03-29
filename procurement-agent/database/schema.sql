-- AI Procurement Agent — PostgreSQL Schema v2
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
    -- Feature 1: notification channels
    phone_number      VARCHAR(50),
    telegram_chat_id  VARCHAR(100),
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
    agent_logs        JSONB DEFAULT '[]',
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
    -- Feature 8: converted INR fields
    inr_unit_price          NUMERIC(12,2),
    inr_total_price         NUMERIC(12,2),
    currency_converted      BOOLEAN DEFAULT FALSE,
    exchange_rate_note      VARCHAR(100),
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

-- ── Feature 5: Quote Validity Tracking ───────────────────────────────────
CREATE TABLE IF NOT EXISTS quote_validity (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quote_id          UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    procurement_id    UUID NOT NULL REFERENCES procurement_requests(id) ON DELETE CASCADE,
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    supplier_name     VARCHAR(255),
    valid_days        INTEGER DEFAULT 30,
    expires_at        TIMESTAMP,
    fetched_at        TIMESTAMP DEFAULT NOW(),
    alert_7day_sent   BOOLEAN DEFAULT FALSE,
    alert_1day_sent   BOOLEAN DEFAULT FALSE,
    is_expired        BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- ── Feature 7: Orders ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quote_id            UUID NOT NULL REFERENCES quotes(id),
    procurement_id      UUID NOT NULL REFERENCES procurement_requests(id),
    supplier_name       VARCHAR(255),
    supplier_url        VARCHAR(500),
    order_id            VARCHAR(255),
    invoice_number      VARCHAR(255),
    total_amount        NUMERIC(12,2),
    estimated_delivery  VARCHAR(255),
    status              VARCHAR(50) DEFAULT 'placing',
    raw                 JSONB,
    placed_at           TIMESTAMP,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ── Feature 10: Supplier Reliability Scores ───────────────────────────────
CREATE TABLE IF NOT EXISTS supplier_scores (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_name       VARCHAR(255) NOT NULL,
    supplier_url        VARCHAR(500) NOT NULL,
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    total_attempts      INTEGER DEFAULT 0,
    successful_quotes   INTEGER DEFAULT 0,
    failed_attempts     INTEGER DEFAULT 0,
    orders_placed       INTEGER DEFAULT 0,
    orders_fulfilled    INTEGER DEFAULT 0,
    avg_response_time_s NUMERIC(8,2) DEFAULT 0,
    avg_delivery_days   NUMERIC(6,2) DEFAULT 0,
    price_accuracy      NUMERIC(5,2) DEFAULT 0,
    reliability_score   NUMERIC(5,2) DEFAULT 50,
    last_updated        TIMESTAMP DEFAULT NOW(),
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_procurement_user     ON procurement_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_procurement   ON quotes(procurement_request_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_category   ON suppliers(category);
CREATE INDEX IF NOT EXISTS idx_suppliers_global     ON suppliers(is_global);
CREATE INDEX IF NOT EXISTS idx_validity_user        ON quote_validity(user_id);
CREATE INDEX IF NOT EXISTS idx_validity_expires     ON quote_validity(expires_at);
CREATE INDEX IF NOT EXISTS idx_orders_user          ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_supplier      ON supplier_scores(supplier_name);