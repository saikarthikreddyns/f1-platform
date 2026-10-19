"""
Data Quality Validation Suite (Step 1.6)
Validates ingested relational F1 data in PostgreSQL:
checks for nulls, impossible lap times, broken stint references, and row counts.
"""

import os
import sys
import dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

dotenv.load_dotenv()

db_params = {
    "dbname": os.getenv("POSTGRES_DB", "f1_platform"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


def run_quality_checks() -> bool:
    """
    Executes data quality checks against PostgreSQL.
    Returns True if all checks pass, False if any check fails.
    """
    conn = psycopg2.connect(**db_params)
    all_passed = True

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("=" * 60)
            print("F1 PLATFORM — DATA QUALITY VALIDATION SUITE")
            print("=" * 60)

            # Check 1: Row count report
            # TODO: Query count(*) for each of the 8 tables and print them.
            # Fail if any core table (seasons, events, sessions, drivers, laps) is 0.
            tables = ["weather", "pit_stops", "laps", "stints", "drivers", "sessions", "events", "seasons"]
            for  table in tables :
                cur.execute(f"SELECT count(*) as cnt FROM {table}")
                cnt = cur.fetchone()["cnt"]
                print(f"Table {table} has {cnt} rows")

                if table in ["seasons", "events", "sessions", "drivers", "laps"] and cnt == 0:
                    print(f"FAIL: Table {table} is empty")
                    all_passed = False

            # Check 2: Critical Null checks
            # TODO: Check for nulls in laps(session_id, driver_id, lap_number)
            # and drivers(abbreviation).
            cur.execute("SELECT COUNT(*) AS cnt FROM laps WHERE session_id IS NULL OR driver_id IS NULL OR lap_number IS NULL")
            null_laps = cur.fetchone()["cnt"]
            if null_laps>0:
                print(f"Fail: Found {null_laps} laps with null identifiers")
                all_passed=False
            else:
                print("Pass: All laps have valid identifiers")

            
            

            # Check 3: Physical Sanity (Lap Times)
            # TODO: Check for impossible lap times (e.g. lap_time_seconds < 45 or > 240)
            # where lap_time_seconds is NOT NULL.
            cur.execute("""SELECT COUNT(*) AS cnt FROM laps 
            WHERE is_accurate = True and lap_time_seconds is not null and lap_time_seconds!='NaN'::float and (lap_time_seconds < 45 OR lap_time_seconds > 240)""")
            impossible_laps = cur.fetchone()["cnt"]
            if impossible_laps>0:
                print(f"Fail: Found {impossible_laps} impossible lap times")
                all_passed=False
            else:
                print("Pass: All lap times are within realistic range")

            # Check 4: Stint Consistency
            # TODO: Check that all laps have stint_id IS NOT NULL,
            # and stints have start_lap <= end_lap and total_laps > 0.
            cur.execute("SELECT COUNT(*) AS cnt FROM laps WHERE stint_id IS NULL")
            null_stints = cur.fetchone()["cnt"]
            if null_stints>0:
                print(f"Fail: Found {null_stints} laps with missing stint ids")
                all_passed=False
            else:
                print("Pass: All laps have valid stint ids")

            # Check 5: Orphan Records
            # TODO: Check for pit_stops or laps with driver_id not matching any driver.
            cur.execute("SELECT COUNT(*) AS cnt FROM pit_stops WHERE driver_id NOT IN (SELECT id FROM drivers)")
            orphan_pit_stops = cur.fetchone()["cnt"]
            if orphan_pit_stops>0:
                print(f"Fail: Found {orphan_pit_stops} pit stops with missing driver ids")
                all_passed=False
            else:
                print("Pass: All pit stops have valid driver ids")

            pass

    finally:
        conn.close()

    return all_passed


if __name__ == "__main__":
    success = run_quality_checks()
    sys.exit(0 if success else 1)
