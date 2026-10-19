create table seasons (
    year int primary key 
);

create table events(
    id uuid primary key default gen_random_uuid(),
    session_year int references seasons(year),
    event_name varchar not null,
    round_number int not null,
    country varchar,
    location varchar,
    session_type varchar ,
    start_time timestamp,
    unique(session_year,round_number)
);

create table sessions(
    id uuid primary key default gen_random_uuid() ,
    event_id uuid references events(id),
    session_name varchar,
    session_type varchar,
    start_time timestamp,
    unique(event_id,session_name)
);

create table drivers(
    id uuid primary key default gen_random_uuid(),
    driver_number int,
    broadcast_name varchar,
    full_name varchar,
    abbreviation varchar,
    team_name varchar
);

create table stints(
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions(id),
    driver_id uuid references drivers(id),
    stint_number int,
    compound varchar,
    start_lap int,
    end_lap int,
    total_laps int,
    unique(session_id,driver_id,stint_number)
);

create table laps(
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions(id),
    driver_id uuid references drivers(id),
    lap_number int,
    lap_time_seconds float,
    sector1_seconds float,
    sector2_seconds float,
    sector3_seconds float,
    compound varchar,
    tyre_life INT,
    is_accurate boolean,
    track_status varchar,
    stint_id uuid references stints(id),
    unique(session_id,driver_id,lap_number)
);

create table pit_stops(
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions(id),
    driver_id uuid references drivers(id),
    stop_number int,
    lap_number int,
    duration_seconds float,
    unique(session_id,driver_id,stop_number)
    
);

create table weather(
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions(id),
    timestamp timestamptz,
    air_temp numeric(5,2) ,
    track_temp numeric(5,2),
    humidity numeric(5,2),
    pressure numeric(6,2),
    rainfall boolean,
    wind_speed numeric(5,1),
    wind_direction varchar(10),
    


    unique(session_id,timestamp)
    
) ;