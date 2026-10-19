"""
Batch Ingestion Pipeline (Step 1.7)
Iterates through full season schedules (2023, 2024, 2025) and loads
race sessions into Postgres and partitioned Parquet telemetry.
"""

import datetime
import fastf1
from ingest import ingest_session
from telemetry import extract_and_save_telemetry
from quality_check import run_quality_checks


SEASONS = [2023, 2024, 2025]


def run_batch_ingest(seasons=SEASONS, session_type: str = "R") -> None:
    now = datetime.datetime.now(datetime.timezone.utc)

    for year in seasons:
        print(f"\n{'=' * 60}")
        print(f"STARTING BATCH INGESTION FOR SEASON {year}")
        print(f"{'=' * 60}")

        schedule = fastf1.get_event_schedule(year)
        # Filter for actual championship races (RoundNumber > 0)
        races = schedule[schedule["RoundNumber"] > 0]

        for _, race in races.iterrows():
            round_num = int(race["RoundNumber"])
            event_name = race["EventName"]
            event_date = race["EventDate"]

            # Skip races that haven't taken place yet
            if hasattr(event_date, "tz_localize"):
                event_date = event_date.tz_localize("UTC")
            elif hasattr(event_date, "tz_convert"):
                event_date = event_date.tz_convert("UTC")
            else:
                event_date = event_date.replace(tzinfo=datetime.timezone.utc)

            if event_date > now:
                print(f"⏭️ Skipping future race: {year} R{round_num} - {event_name}")
                continue

            print(f"\n>>> [{year} | Round {round_num}] Ingesting {event_name}...")
            try:
                # 1. Ingest relational data into PostgreSQL
                ingest_session(year, round_num, session_type)

                # 2. Extract and save telemetry into Parquet
                extract_and_save_telemetry(year, round_num, session_type)

            except Exception as e:
                print(f"⚠️ Error ingesting {year} R{round_num} ({event_name}): {e}")
                print("Continuing with next race...")

    print(f"\n{'=' * 60}")
    print("🏁 Batch ingestion finished. Running Data Quality Checks...")
    print(f"{'=' * 60}")
    run_quality_checks()


if __name__ == "__main__":
    run_batch_ingest()
