import requests
import sqlite3,time
from datetime import datetime
from datetime import datetime
import get_pair

#  ==========================================================
BINANCE_API_URL = "https://api.binance.com/api/v3/exchangeInfo"

def get_usdt_pairs() -> list: 
    """جلب فقط الأزواج التي يتم تداولها مقابل USDT"""
    response = requests.get(BINANCE_API_URL)
    if response.status_code == 200:
        data = response.json()
        usdt_pairs = set()
        for symbol in data['symbols']:
            if symbol['status'] == 'TRADING' and 'USDT' in symbol['symbol']:
                usdt_pairs.add(symbol['symbol'])
    
        return usdt_pairs
    else:
        print("⚠️ خطأ في جلب البيانات من Binance")
        return []
#  ==========================================================
def get_pair_info(symbol: str):
    url = f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data["symbols"][0]
    else:
        print(f"Error fetching data for {symbol}")
        return None


# ===================================================================================

def binance_crypto(): # ===> To compare the piars of binance
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            new_pairs = get_usdt_pairs()
            old_pairs = get_pair.get_symboles(g="binance",db=db)
            compare_pairs = new_pairs - old_pairs
            if compare_pairs:
                print(f"new pair detected{compare_pairs}")
                for f in compare_pairs:
                    cursor.execute("INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f),"binance",str(datetime.now().timestamp())))
                    pair_info = get_pair_info(f)
                    cursor.execute("INSERT INTO binance (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseAsset"]),str(pair_info["quoteAsset"]),str(datetime.now().timestamp())))
                    db.commit()
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(10)
