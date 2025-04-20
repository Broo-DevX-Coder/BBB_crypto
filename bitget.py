import httpx

# تحميل البيانات مرة واحدة وتخزينها داخليًا
_cached_symbol_data = None

def fetch_symbol_data():
        global _cached_symbol_data
    
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                _cached_symbol_data = data.get('data', [])
            else:
                print(f"Error: {response.status_code}")
                _cached_symbol_data = []

        except httpx.RequestError as e:
            print(f"Request error: {e}")
            _cached_symbol_data = []

        return _cached_symbol_data


def get_all_trading_pairs() -> list:
    trading_pairs = fetch_symbol_data()
    pairs_info = [
        pair['symbol']
        for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
    ]
    return set(pairs_info)


def get_pair_info(symbol: str):
    symbols = fetch_symbol_data()
    for pair in symbols:
        if pair['symbol'] == symbol:
            return pair

    print(f"زوج {symbol} غير موجود في قائمة الأزواج المتاحة")
    return None
