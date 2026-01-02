#!/bin/bash
set -e

# This script initializes the PostgreSQL database with the required user and database.
# It runs on first container startup if the data volume is empty.

# Create the research user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Ensure the research role exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'research') THEN
            CREATE ROLE research WITH LOGIN PASSWORD 'research';
        END IF;
    END
    \$\$;
    
    -- Grant all privileges on the database
    GRANT ALL PRIVILEGES ON DATABASE research_db TO research;
    
    -- Grant all privileges on schema public
    GRANT ALL PRIVILEGES ON SCHEMA public TO research;
    
    -- Ensure research can create tables
    ALTER ROLE research CREATEDB;
EOSQL

echo "Database initialization complete!"
