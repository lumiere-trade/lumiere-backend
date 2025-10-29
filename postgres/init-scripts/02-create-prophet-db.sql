-- ============================================================
-- PROPHET DATABASE INITIALIZATION
-- ============================================================
-- Auto-executes on first Postgres container startup
-- Creates prophet_user and three databases: prod, dev, test
--
-- This script is idempotent - safe to run multiple times
-- ============================================================

-- Create user
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'prophet_user'
    ) THEN
        CREATE USER prophet_user WITH PASSWORD 'prophet_pass';
        RAISE NOTICE 'User prophet_user created';
    ELSE
        RAISE NOTICE 'User prophet_user already exists';
    END IF;
END
$$;

-- Create production database (no suffix)
SELECT 'CREATE DATABASE prophet_db OWNER prophet_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'prophet_db'
)\gexec

-- Create development database
SELECT 'CREATE DATABASE prophet_dev_db OWNER prophet_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'prophet_dev_db'
)\gexec

-- Create test database
SELECT 'CREATE DATABASE prophet_test_db OWNER prophet_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'prophet_test_db'
)\gexec

-- Grant privileges on all databases
GRANT ALL PRIVILEGES ON DATABASE prophet_db TO prophet_user;
GRANT ALL PRIVILEGES ON DATABASE prophet_dev_db TO prophet_user;
GRANT ALL PRIVILEGES ON DATABASE prophet_test_db TO prophet_user;

-- Setup schema privileges for production database
\c prophet_db
GRANT ALL PRIVILEGES ON SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO prophet_user;

-- Setup schema privileges for development database
\c prophet_dev_db
GRANT ALL PRIVILEGES ON SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO prophet_user;

-- Setup schema privileges for test database
\c prophet_test_db
GRANT ALL PRIVILEGES ON SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prophet_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO prophet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO prophet_user;

-- Success message
\echo 'Prophet database initialization completed successfully'
\echo 'Created databases: prophet_db (prod), prophet_dev_db, prophet_test_db'
