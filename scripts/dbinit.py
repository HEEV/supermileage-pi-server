from os import getenv

import psycopg2

conn = psycopg2.connect(
    database=getenv("DB"),
    host=getenv("DB_HOST"),
    user=getenv("DB_USER"),
    password=getenv("DB_PASSWORD"),
    port=getenv("DB_PORT"),
)

cursor = conn.cursor()

# create table for db
cursor.execute("""
create table if not exists car_data (
    car_id int,
    time int,
    voltage float,
    speed float,
    distance_traveled float,
    primary key (car_id, time)
""")
