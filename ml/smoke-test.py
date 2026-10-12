import fastf1
import pathlib
import os 

# choosing cache folder

cache_dir = pathlib.Path(__file__).resolve().parent.parent / "data" / "cache"
if cache_dir.exists():
    print("cache folder already exists")
else:
    cache_dir.mkdir()
fastf1.Cache.enable_cache(cache_dir)

#loading session
session = fastf1.get_session(2023,'Bahrain',"R")
session.load(telemetry=False,weather=False)

print("session loaded, let's check telemetry")
laps = session.laps

print(laps.head(10))