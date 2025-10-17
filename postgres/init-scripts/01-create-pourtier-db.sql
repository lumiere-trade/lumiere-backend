-- ============================================================
-- POURTIER DATABASE INITIALIZATION
-- ============================================================
-- Auto-executes on first Postgres container startup
-- Creates pourtier_user and pourtier_test_db
--
-- This script is idempotent - safe to run multiple times
-- ============================================================

-- Create user
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pourtier_user'
    ) THEN
        CREATE USER pourtier_user WITH PASSWORD 'pourtier_pass';
        RAISE NOTICE 'User pourtier_user created';
    ELSE
        RAISE NOTICE 'User pourtier_user already exists';
    END IF;
END
$$;

-- Create database
SELECT 'CREATE DATABASE pourtier_test_db OWNER pourtier_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'pourtier_test_db'
)\gexec

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE pourtier_test_db TO pourtier_user;

-- Connect to pourtier_test_db and setup schema privileges
\c pourtier_test_db

-- Grant all privileges on public schema
GRANT ALL PRIVILEGES ON SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pourtier_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO pourtier_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO pourtier_user;

-- Success message
\echo '✅ Pourtier database initialization completed successfully'
