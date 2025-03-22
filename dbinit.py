import psycopg2


conn = psycopg2.connect(database="b75mloimvzz5rvv5xcdk",
                                host="b75mloimvzz5rvv5xcdk-postgresql.services.clever-cloud.com",
                                user="uoh8y5okijoz5xxdiqit",
                                password="qFhTMlsKuzHqobkU2z24AzIOxXYisS",
                                port="50013")

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
