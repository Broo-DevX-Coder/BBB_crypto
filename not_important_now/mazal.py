"""
from dotenv import load_dotenv
import logging,hmac,os
from hashlib import sha256
import flask

# =================
load_dotenv("/opt/per/def_python_env/BBB.env")
# =================
API = str(os.getenv("Bitget_API"))
Secret_key = str(os.getenv("Bitget_Secret_key"))
Password = str(os.getenv("Bitget_Password"))
# ================"
"""
import sqlite3
db = sqlite3.connect("Crypto.db")
cursor = db.cursor()
cursor.execute('DELETE FROM new')
db.commit()
db.close()