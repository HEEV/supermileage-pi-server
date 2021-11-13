from reader import Reader
import sqlite3
from sqlite3 import Error
import os

# Set up a reader to get data
reader = Reader(os.environ.get('PICO_DEV'))

# Connect to the database
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(e)
    return connection

# Open the connnection
connection = create_connection("data/test.db")
