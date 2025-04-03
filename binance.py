import requests

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


