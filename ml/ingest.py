#database connection 
from fastf1._api import weather_data
import dotenv
import os
import pathlib
import fastf1
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import math 
dotenv.load_dotenv()
db_params = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

#enable fastf1 cache
cache_path = pathlib.Path(__file__).resolve().parent.parent / "data" / "fastf1_cache"
cache_path.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(cache_path))



#
# Helpers
#

def clean(value):
    """Converting missing values into None"""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except(TypeError,ValueError):
        pass
    return value

def to_seconds(value):
    """Convert time strings(mm:ss.SSS) to seconds."""
    if value is None:
        return None
    if hasattr(value,"total_seconds"):
        val = value.total_seconds()
        return None if (val is None or math.isnan(val)) else float(val)
    try:
        val = float(value)
        return None if math.isnan(val) else val
    except(ValueError,TypeError):
        return None
    

def to_int(value):
    value = clean(value)
    return int(value) if value is not None else None

def to_str(value):
    value = clean(value)
    return str(value) if value is not None else None



#insert season event session
def ingest_session(year,round_or_name,session_type):
    print(f"Loading FastF1 Session:"
    f"{year} , {round_or_name},{session_type}"
    "\n---------------------------------------------------------")
    session = fastf1.get_session(year,round_or_name,session_type)
    session.load()

    event = session.event
    results = session.results
    laps = session.laps
    weather_data = session.weather_data
    

    event_name = str(event["EventName"])
    round_number = int(event["RoundNumber"])
    country = clean(event.get("Country"))
    location = clean(event.get("Location"))
    session_name = str(session.name)
    start_time = clean(session.date)

    #A single transaction protects all ingestion steps
    conn = psycopg2.connect(**db_params)

    try:
        with conn:
            with conn.cursor() as cur:
                #session
                cur.execute("""
                INSERT INTO seasons(year) values (%s) 
                on conflict (year) do nothing
                """,
                (year,),
                )
                #events
                cur.execute(
                    """
                    insert into events(
                    SESSION_YEAR,EVENT_NAME,ROUND_NUMBER,
                    COUNTRY,LOCATION,SESSION_TYPE,START_TIME)
                    values(%s,%s,%s,%s,%s,%s,%s)
                    on conflict (SESSION_YEAR,ROUND_NUMBER)
                    do update
                    set event_name = EXCLUDED.event_name,
                    COUNTRY = EXCLUDED.COUNTRY,
                    LOCATION = EXCLUDED.LOCATION,
                    SESSION_TYPE = EXCLUDED.SESSION_TYPE,
                    START_TIME = EXCLUDED.START_TIME
                    returning id
                    """,
                    (year,event_name,round_number,country,location,
                    session_type,start_time),
                )
                event_id = cur.fetchone()[0]
                
                #sessions
                cur.execute("""
                insert into sessions(
                event_id,session_name,session_type,start_time)
                values(%s,%s,%s,%s)
                on conflict (event_id,session_name) do update set
                session_type =EXCLUDED.session_type,
                start_time = EXCLUDED.start_time
                returning id
                """,(event_id,session_name,session_type,start_time),)
                session_id = cur.fetchone()[0]
                
                #drivers
                driver_lookup = {}
                for _,driver in results.iterrows():
                    abbreviation = to_str(driver.get("Abbreviation"))
                    driver_number = to_int(driver.get("DriverNumber"))
                    if not abbreviation:
                        continue
                    cur.execute("""
                    SELECT id
                    from drivers
                    where abbreviation = %s
                    order by id
                    limit 1
                    """,
                    (abbreviation,),)
                    existing = cur.fetchone()
                    if existing:
                        driver_id = existing[0]
                        cur.execute(
                            """
                            UPDATE DRIVERS
                            SET DRIVER_NUMBER = %s,
                            broadcast_name = %s,
                            full_name = %s,
                            team_name=%s
                            where id = %s
                            """,
                            (
                                driver_number,to_str(driver.get("BroadcastName")),
                                to_str(driver.get("FullName")),
                                to_str(driver.get("TeamName")),
                                driver_id,
                            ),
                        )
                    else:
                        cur.execute("""
                        insert into drivers(
                        driver_number,
                        broadcast_name,
                        full_name,
                        team_name,
                        abbreviation)
                        values(%s,%s,%s,%s,%s)
                        returning id
                        """,(driver_number,to_str(driver.get("BroadcastName")),
                        to_str(driver.get("FullName")),to_str(driver.get("TeamName")),abbreviation,),
                        )
                        driver_id = cur.fetchone()[0]
                    driver_lookup[abbreviation] = driver_id

                #stints

                stint_lookup = {}
                if not laps.empty:
                    valid_stincts = laps.dropna(
                        subset = ["Driver","Stint","LapNumber"],
                    )

                    for(driver_code,stint_number),group in (valid_stincts.groupby(["Driver","Stint"])):
                        driver_id=driver_lookup.get(str(driver_code))
                        if driver_id is None:
                            continue
                        stint_number = int(stint_number)
                        start_lap = int(group["LapNumber"].min())
                        end_lap = int(group["LapNumber"].max())
                        total_laps = int(group["LapNumber"].nunique())

                        compound = None

                        if "Compound" in group.columns:
                            compounds = group["Compound"].dropna()

                            if not compounds.empty:
                                compound =  to_str(compounds.iloc[0])

                        cur.execute("""
                        INSERT INTO Stints(
                             SESSION_ID,DRIVER_ID,STINT_NUMBER,COMPOUND,
                            START_LAP,END_LAP,TOTAL_LAPS
                        )
                        VALUES(%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(
                        session_id,driver_id,stint_number
                        )
                        DO UPDATE 
                        SET 
                            START_LAP=EXCLUDED.START_LAP,
                            END_LAP=EXCLUDED.END_LAP,
                            TOTAL_LAPS=EXCLUDED.TOTAL_LAPS,
                            COMPOUND=EXCLUDED.COMPOUND
                        RETURNING ID
                        """,(
                            session_id,driver_id,stint_number,
                            compound,start_lap,end_lap,total_laps,),
                            )
                        stint_id = cur.fetchone()[0] 
                        stint_lookup[(driver_id,stint_number)]=stint_id      

                #laps 
                if not laps.empty:
                    for _,lap in laps.iterrows():
                        
                        driver_id = driver_lookup.get(to_str(lap["Driver"]))
                        if driver_id is None:
                            continue
                        stint_number = int(lap["Stint"])
                        lap_number = int(lap["LapNumber"])
                        lap_time_seconds = to_seconds(lap["LapTime"])
                        sector1_seconds = to_seconds(lap["Sector1Time"])
                        sector2_seconds = to_seconds(lap["Sector2Time"])
                        sector3_seconds = to_seconds(lap["Sector3Time"])
                        compound = to_str(lap["Compound"])
                        tyre_life = to_int(lap.get("TyreLife"))
                        stint_id = stint_lookup.get((driver_id,stint_number))
                        track_status = to_str(lap.get("TrackStatus"))
                        is_accurate = bool(lap.get("IsAccurate"))
                        
                        cur.execute("""
                       INSERT INTO LAPS(SESSION_ID,DRIVER_ID,
                       LAP_NUMBER,LAP_TIME_SECONDS,SECTOR1_SECONDS,
                       SECTOR2_SECONDS,SECTOR3_SECONDS,COMPOUND,TYRE_LIFE,STINT_ID,
                       TRACK_STATUS,IS_ACCURATE)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(
                       session_id,driver_id,lap_number)
                       DO UPDATE SET 
                       TRACK_STATUS = EXCLUDED.TRACK_STATUS,
                       IS_ACCURATE = EXCLUDED.IS_ACCURATE,
                       lap_time_seconds=EXCLUDED.LAP_TIME_SECONDS,
                       compound = EXCLUDED.compound
                       
                       RETURNING ID
                       """,(
                        session_id,driver_id,
                        lap_number,lap_time_seconds,
                        sector1_seconds,sector2_seconds,
                        sector3_seconds,compound,
                        tyre_life,stint_id,
                        track_status,is_accurate),
                        )
                
                #pit stops
                if not laps.empty:
                    pit_laps = laps[laps["PitInTime"].notna()]
                    for _,pit_stop in pit_laps.iterrows():
                        driver_id = driver_lookup.get(to_str(pit_stop["Driver"]))
                        if driver_id is None:
                            continue
                        stop_number = to_int(pit_stop.get("Stint"))
                        lap_number = to_int(pit_stop.get("LapNumber"))
                        duration_seconds=to_seconds(pit_stop.get("PitDuration")) 

                        cur.execute("""
                        INSERT INTO PIT_STOPS(
                        SESSION_ID,DRIVER_ID,STOP_NUMBER,LAP_NUMBER,DURATION_SECONDS)
                        VALUES(%s,%s,%s,%s,%s)
                        ON CONFLICT(
                        session_id,driver_id,stop_number)
                        DO UPDATE SET 
                        LAP_NUMBER=EXCLUDED.LAP_NUMBER,
                        DURATION_SECONDS=EXCLUDED.DURATION_SECONDS
                        RETURNING ID
                        """,(
                            session_id,driver_id,
                            stop_number,lap_number,
                            duration_seconds),)
                
                #weather
                if weather_data is not None and not weather_data.empty:
                    for _,weather in weather_data.iterrows():
                        timestamp = session.date + weather["Time"]
                        air_temp = float(weather.get("AirTemp"))
                        track_temp = float(weather.get("TrackTemp"))
                        humidity = float(weather.get("Humidity"))
                        pressure = float(weather.get("Pressure"))
                        rainfall = bool(weather.get("Rainfall"))
                        wind_speed = float(weather.get("WindSpeed"))
                        wind_direction = to_str(weather.get("WindDirection"))
                        cur.execute("""
                        INSERT INTO WEATHER(
                        SESSION_ID,TIMESTAMP,AIR_TEMP,TRACK_TEMP,
                        HUMIDITY,PRESSURE,RAINFALL,WIND_SPEED,WIND_DIRECTION)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(
                        session_id,timestamp)
                        DO UPDATE SET 
                        AIR_TEMP=EXCLUDED.AIR_TEMP,
                        TRACK_TEMP=EXCLUDED.TRACK_TEMP,
                        HUMIDITY=EXCLUDED.HUMIDITY,
                        PRESSURE=EXCLUDED.PRESSURE,
                        RAINFALL=EXCLUDED.RAINFALL,
                        WIND_SPEED=EXCLUDED.WIND_SPEED,
                        WIND_DIRECTION=EXCLUDED.WIND_DIRECTION
                        RETURNING ID
                        """,(
                            session_id,timestamp,
                            air_temp,track_temp,
                            humidity,pressure,
                            rainfall,wind_speed,
                            wind_direction,),
                            )
                
                conn.commit()
                print("Done-Ingesting-Session",event_name)
        
    finally:
        if conn:
            conn.close()
    
if __name__ == "__main__":
    ingest_session(2023,1,"R")
    

                        
                        
                        
                        

                