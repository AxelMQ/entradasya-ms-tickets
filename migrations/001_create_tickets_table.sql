-- Migration: 001_create_tickets_table.sql
-- Description: Create tickets table and indexes for ms-tickets

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    event_id UUID NOT NULL,
    event_title VARCHAR(200) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL,
    venue VARCHAR(200) NOT NULL,
    sector_name VARCHAR(100) NOT NULL,
    customer_id UUID NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(150) NOT NULL,
    ticket_code VARCHAR(64) NOT NULL UNIQUE,
    pdf_filename VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ISSUED' CHECK (status IN ('ISSUED', 'CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_code ON tickets(ticket_code);
CREATE INDEX IF NOT EXISTS idx_tickets_order_id ON tickets(order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_event_id ON tickets(event_id);
