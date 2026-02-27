#!/usr/bin/env bash
set -e

echo "Restoring database into '$DB_NAME'..."

# Run restore as postgres superuser
pg_restore \
  --no-owner \
  --no-privileges \
  -U postgres \
  -d "$DB_NAME" \
  /tmp/restore.pgdump

echo "Restore complete."

# Create read-only user if DB_USER is set
if [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
  echo "Creating read-only user '$DB_USER'..."

  psql -v ON_ERROR_STOP=1 -U postgres -d "$DB_NAME" <<-EOSQL
    -- Create the read-only user
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

    -- Grant connect privilege
    GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;

    -- Grant usage on public schema
    GRANT USAGE ON SCHEMA public TO $DB_USER;

    -- Grant select on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO $DB_USER;

    -- Grant usage on all sequences (for reading sequence values)
    GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

    -- Grant execute on all functions (read-only functions)
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;
EOSQL

  echo "Read-only user created successfully."
fi

# Create completion marker
echo "Database initialization complete at $(date)" > /var/lib/postgresql/restore_complete
echo "Database restore and setup complete."