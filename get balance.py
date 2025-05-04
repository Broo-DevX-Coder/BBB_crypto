import time
import hmac
import hashlib
import base64
import httpx
import json


API_KEY = "bg_4b9f427195498f567a3dea139db96581"
API_SECRET = "4580e37c3fe159e61528b86df0144f66fc35e403361014c98659d9bb8657e817"
PASSPHRASE = "123baba456"


def generate_signature(timestamp, method, request_path, body=''):
    prehash = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        prehash.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()


def get_balance():
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    url = "https://api.bitget.com/api/v2/spot/account/assets"
    sign = generate_signature(timestamp, method, "/api/v2/spot/account/assets")
    
    
    response = httpx.get(url, headers={
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE
    })
    
    if response.status_code == 200:
        data = response.json()
        assests = {
                    str(ass["coin"]):{
                        "amount":str(ass["available"]),
                        "frozen":str(ass["frozen"])
                    } 
                    for ass in data["data"] }
        print(assests)
    else:
        print("❌ Error fetching balance:", response.text)

get_balance()

