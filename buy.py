import time
import hmac
import hashlib
import base64
import httpx
import json

# بيانات حسابك من Bitget
API_KEY = "bg_4b9f427195498f567a3dea139db96581"
API_SECRET = "4580e37c3fe159e61528b86df0144f66fc35e403361014c98659d9bb8657e817"
PASSPHRASE = "123baba456"



def get_current_price(symbol="BNBUSDT"):
    url = f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}"
    response = httpx.get(url)
    
    if response.status_code == 200:
        data = response.json()
        price = data['data'][0]["lastPr"] # السعر الحالي
        return float(price)
    else:
        print("Error fetching price:", response.text)
        return None

# HMAC signature
def generate_signature(timestamp, method, request_path, body=''):
    prehash = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        prehash.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

# تنفيذ أمر شراء أو بيع
def place_order(symbol, side, price, size):
    url = "https://api.bitget.com/api/v2/spot/trade/place-order"
    method = "POST"
    timestamp = str(int(time.time() * 1000))
    body = {
        "symbol": symbol,      # مثل "BTCUSDT"
        "side": side,          # "buy" أو "sell"
        "orderType": "limit",  # أو "market"
        "price": str(price),   # إذا limit فقط
        "size": f"{size:.4f}",      # كمية الشراء أو البيع
        "force":"gtc"
    }
    body_str = json.dumps(body)
    sign = generate_signature(timestamp, method, "/api/v2/spot/trade/place-order", body_str)

    headers = {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE
    }

    response = httpx.post(url, headers=headers, data=body_str)
    print(response.status_code, response.text)

# مثال: شراء 0.001 BTC بسعر 30000 USDT

se = 10 / get_current_price()
print(get_current_price()*se)
place_order("BNBUSDT", "buy", price=100, size=se)
