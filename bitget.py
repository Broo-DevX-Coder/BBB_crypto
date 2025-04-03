import requests

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