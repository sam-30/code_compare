-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Test database
CREATE DATABASE codecmp_test;
GRANT ALL PRIVILEGES ON DATABASE codecmp_test TO codecmp;

-- Default comparison config will be inserted after migrations run via a startup script.
-- See backend/app/db/seed.py
