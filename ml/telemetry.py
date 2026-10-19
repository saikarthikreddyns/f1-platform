"""
Telemetry Ingestion Pipeline (Step 1.4)
Extracts high-frequency sensor streams from FastF1 and stores them
in partitioned Apache Parquet format.
"""

from typing import Any
import pathlib
import fastf1
import pandas as pd


# FastF1 Cache setup
CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

# Base output directory for telemetry Parquet files
TELEMETRY_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "telemetry"


def extract_and_save_telemetry(year: int, round_or_name, session_type: str = "R") -> None:
    """
    Loads a session, extracts car telemetry for every driver,
    and saves each driver's telemetry partitioned by season/round/driver.
    """
    # 1. Load the FastF1 session
    # TODO: Load session (make sure telemetry=True)
    session = fastf1.get_session(year,round_or_name,session_type)
    session.load(telemetry=True,laps=True)
    round_num = int(session.event["RoundNumber"])

    # 2. Iterate through each driver
    # TODO: For each driver code:
    #       - filter laps for that driver
    #       - call .get_telemetry()
    #       - ensure partition metadata (season, round, driver) exists if needed
    #       - create target directory: TELEMETRY_DIR / f"season={year}" / f"round={round_num}" / f"driver={code}"
    #       - save to parquet using DataFrame.to_parquet(...)
    for _,driver_code in session.results['Abbreviation'].items():
        driver_laps = session.laps.pick_drivers(driver_code)
        if driver_laps.empty:
            continue

        tele = driver_laps.get_telemetry()
        if tele.empty:
            continue
        out_dir = TELEMETRY_DIR/f"season={year}"/f"round={round_num}"/f"driver={driver_code}"
        out_dir.mkdir(parents=True,exist_ok=True)
        file_path = out_dir/"telemetry.parquet"
        tele.to_parquet(file_path, engine="pyarrow", index=False)
        print(f"Saved {driver_code} telemetry {len(tele)} rows.")


    print("Telemetry ingestion is complete.")

     

    

    


if __name__ == "__main__":
    extract_and_save_telemetry(2023, 1, "R")
