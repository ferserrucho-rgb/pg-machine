"""
Data migration script: Supabase → Neon PostgreSQL.
Exports all 9 tables from Supabase and imports into Neon.

Usage:
    pip install supabase psycopg2-binary bcrypt
    python neon/migrations/002_data_migration.py

Requires environment variables:
    SUPABASE_URL, SUPABASE_SERVICE_KEY, NEON_DATABASE_URL
"""
import os
import sys
import json
import bcrypt
import psycopg2
from psycopg2 import extras
from supabase import create_client

# --- Config ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
NEON_DATABASE_URL = os.environ.get("NEON_DATABASE_URL", "")

# Temporary password hash for migrated users (they must reset on first login)
TEMP_PASSWORD = "changeme123"
TEMP_HASH = bcrypt.hashpw(b"$2b$12$TEMPchangeme123placeholder", bcrypt.gensalt()).decode()
# Use a recognizable prefix so auth.py can detect it
TEMP_HASH_REAL = bcrypt.hashpw(TEMP_PASSWORD.encode(), b"$2b$12$TEMP000000000000000000").decode()


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_neon():
    if not NEON_DATABASE_URL:
        print("ERROR: Set NEON_DATABASE_URL environment variable")
        sys.exit(1)
    return psycopg2.connect(NEON_DATABASE_URL)


def export_table(sb, table_name: str, order_col: str = "created_at") -> list[dict]:
    """Export all rows from a Supabase table."""
    resp = sb.table(table_name).select("*").order(order_col).execute()
    rows = resp.data or []
    print(f"  Exported {len(rows)} rows from {table_name}")
    return rows


def insert_rows(conn, table_name: str, rows: list[dict], extra_cols: dict | None = None):
    """Insert rows into Neon table."""
    if not rows:
        print(f"  Skipping {table_name} (no rows)")
        return
    for row in rows:
        if extra_cols:
            row.update(extra_cols)
        # Handle JSONB columns: serialize dicts/lists to JSON strings
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                row[k] = json.dumps(v)

    cols = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    values = [tuple(row.get(c) for c in cols) for row in rows]

    with conn.cursor() as cur:
        extras.execute_batch(
            cur,
            f'INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING',
            values,
        )
    conn.commit()
    print(f"  Inserted {len(rows)} rows into {table_name}")


def main():
    print("=== PG Machine: Supabase → Neon Data Migration ===\n")

    # 1. Connect
    print("Connecting to Supabase...")
    sb = get_supabase()
    print("Connecting to Neon...")
    conn = get_neon()

    # 2. Export from Supabase
    print("\n--- Exporting from Supabase ---")
    teams = export_table(sb, "teams")
    profiles = export_table(sb, "profiles")
    opportunities = export_table(sb, "opportunities")
    activities = export_table(sb, "activities")
    notifications = export_table(sb, "notifications")
    team_config = export_table(sb, "team_config")

    # These may not exist in older schemas — handle gracefully
    try:
        calendar_inbox = export_table(sb, "calendar_inbox")
    except Exception:
        calendar_inbox = []
        print("  calendar_inbox: table not found, skipping")
    try:
        pipeline_snapshots = export_table(sb, "pipeline_snapshots")
    except Exception:
        pipeline_snapshots = []
        print("  pipeline_snapshots: table not found, skipping")
    try:
        viajes = export_table(sb, "viajes")
    except Exception:
        viajes = []
        print("  viajes: table not found, skipping")

    # 3. Transform profiles: add password_hash
    print("\n--- Transforming profiles ---")
    for p in profiles:
        p["password_hash"] = TEMP_HASH_REAL
        # Ensure lang column
        p.setdefault("lang", "es")
    print(f"  Added temporary password hash to {len(profiles)} profiles")

    # 4. Import into Neon (FK order)
    print("\n--- Importing into Neon ---")
    insert_rows(conn, "teams", teams)
    insert_rows(conn, "profiles", profiles)
    insert_rows(conn, "opportunities", opportunities)
    insert_rows(conn, "activities", activities)
    insert_rows(conn, "notifications", notifications)
    insert_rows(conn, "team_config", team_config)
    insert_rows(conn, "calendar_inbox", calendar_inbox)
    insert_rows(conn, "pipeline_snapshots", pipeline_snapshots)
    insert_rows(conn, "viajes", viajes)

    conn.close()
    print("\n=== Migration complete! ===")
    print(f"All users have temporary password '{TEMP_PASSWORD}'.")
    print("They will be prompted to set a new password on first login.")


if __name__ == "__main__":
    main()
