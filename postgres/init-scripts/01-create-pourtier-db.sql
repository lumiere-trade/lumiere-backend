-- ============================================================
-- POURTIER DATABASE INITIALIZATION
-- ============================================================
-- Auto-executes on first Postgres container startup
-- Creates pourtier_user and three databases: prod, dev, test
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

-- Create production database (no suffix)
SELECT 'CREATE DATABASE pourtier_db OWNER pourtier_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'pourtier_db'
)\gexec

-- Create development database
SELECT 'CREATE DATABASE pourtier_dev_db OWNER pourtier_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'pourtier_dev_db'
)\gexec

-- Create test database
SELECT 'CREATE DATABASE pourtier_test_db OWNER pourtier_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'pourtier_test_db'
)\gexec

-- Grant privileges on all databases
GRANT ALL PRIVILEGES ON DATABASE pourtier_db TO pourtier_user;
GRANT ALL PRIVILEGES ON DATABASE pourtier_dev_db TO pourtier_user;
GRANT ALL PRIVILEGES ON DATABASE pourtier_test_db TO pourtier_user;

-- Setup schema privileges for production database
\c pourtier_db
GRANT ALL PRIVILEGES ON SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO pourtier_user;

-- Setup schema privileges for development database
\c pourtier_dev_db
GRANT ALL PRIVILEGES ON SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO pourtier_user;

-- Setup schema privileges for test database
\c pourtier_test_db
GRANT ALL PRIVILEGES ON SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO pourtier_user;

-- Success message
\echo 'Pourtier database initialization completed successfully'
\echo 'Created databases: pourtier_db (prod), pourtier_dev_db, pourtier_test_db'
