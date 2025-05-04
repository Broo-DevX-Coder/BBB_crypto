import sqlite3
import os
BASE_DIR = os.path.dirname(__file__)
DB_NAME = "Local.db"
DB_DIR = os.path.join(BASE_DIR, DB_NAME)
db = sqlite3.connect(DB_DIR, autocommit=True)
cursor = db.cursor()
cursor.execute("DELETE FROM bitget WHERE symbol='BNBUSDT' ")
db.close()