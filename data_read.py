from reader import Reader
import os
import time
import mysql.connector
from mysql.connector import errorcode

# Set up a reader to get data
reader = Reader(os.environ.get('PICO_DEV'))

try:
    # Connect to the dataabase
    cnx = mysql.connector.connect(
        user='server', password='password', host='127.0.0.1', database='super_mileage_test')
except mysql.connector.Error as err:

    # Handle errors
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    while True:
        # Create a query
        cursor = cnx.cursor()
        query = ("SELECT * FROM main WHERE time=(SELECT MAX(time) FROM main);")

        # Execute the query
        cursor.execute(query)

        for (time, number) in cursor:
            print(f"{time}: {number}")
