import requests
import sqlite3,time
from datetime import datetime
from datetime import datetime
import get_pair

def get_all_trading_pairs() -> list:
    url = 'https://api.bitget.com/api/v2/spot/public/symbols'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        trading_pairs = data.get('data', [])
        pairs_info = [
            pair['symbol']
            for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
        ]

        return set(pairs_info)
    else:
        print(f"Error: {response.status_code}")
        return []


def get_pair_info(symbol: str):
    url = 'https://api.bitget.com/api/v2/spot/public/symbols'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        symbols = data.get("data", [])
        
        # البحث عن الزوج المطلوب في البيانات
        for pair in symbols:
            if pair['symbol'] == symbol:
                return pair
        print(f"زوج {symbol} غير موجود في قائمة الأزواج المتاحة")
        return None
    else:
        print(response.status_code)
        return None
    
# def branch ===================================================================================================


def bitget_crypto(): # ===> To compare the piars of bitget
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            new_pairs = get_all_trading_pairs()
            old_pairs = get_pair.get_symboles(g="bitget",db=db)
            compare_pairs = new_pairs - old_pairs
            if compare_pairs:
                print(f"new pair detected{compare_pairs}")
                for f in compare_pairs:
                    cursor.execute("INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f),"bitget",str(datetime.now().timestamp())))
                    pair_info = get_pair_info(f)
                    cursor.execute("INSERT INTO bitget (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseAsset"]),str(pair_info["quoteAsset"]),str(datetime.now().timestamp())))
                    db.commit()
                    get_pair.sand_TLG_msg("Bitget",str(pair_info["symbol"]))
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(10)