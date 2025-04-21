import httpx

# تحميل البيانات مرة واحدة وتخزينها داخليًا
_cached_symbol_data = None

def fetch_symbol_data():  # this functon return 3 values ( Pairs / Error_type / Error_info )
        global _cached_symbol_data
    
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                _cached_symbol_data = data.get('data', [])
                return _cached_symbol_data,None,None 
            else:
                _cached_symbol_data = []
            return _cached_symbol_data,"response_code",str(response.status_code)

        except httpx.RequestError as e:
            _cached_symbol_data = []
            return _cached_symbol_data,"request_code",str(e)


        


def get_all_trading_pairs(): # this functon return 3 values ( Pairs / Error_type / Error_info )
    trading_pairs,error_type,error_info = fetch_symbol_data()
    pairs_info = [
        pair['symbol']
        for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
    ]
    return set(pairs_info),error_type,error_info


def get_pair_info(symbol: str): # this functon return 3 values ( Pairs / Error_type / Error_info )

    symbols,e,r = fetch_symbol_data()

    for pair in symbols:
        if pair['symbol'] == symbol:
            return pair,None,None
        
    return None,"Not_found","this pair not found !!"
