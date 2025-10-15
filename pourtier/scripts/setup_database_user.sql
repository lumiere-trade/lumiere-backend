-- ============================================================
-- POURTIER DATABASE USER SETUP
-- ============================================================
-- Creates PostgreSQL user and database with proper permissions
-- Run this script as postgres superuser
-- ============================================================

-- Create user if not exists
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

-- Create database if not exists
SELECT 'CREATE DATABASE pourtier_db OWNER pourtier_user'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'pourtier_db'
)\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pourtier_db TO pourtier_user;

-- Connect to pourtier_db and grant schema privileges
\c pourtier_db

GRANT ALL PRIVILEGES ON SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pourtier_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pourtier_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT ALL PRIVILEGES ON TABLES TO pourtier_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT ALL PRIVILEGES ON SEQUENCES TO pourtier_user;

\echo 'Database user setup completed successfully!'
