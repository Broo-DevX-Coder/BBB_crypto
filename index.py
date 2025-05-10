import os, subprocess, sys, requests, sqlite3, time, hmac, hashlib, base64, json, httpx, math
from threading import Thread
from dotenv import load_dotenv
from datetime import datetime
from requests.adapters import HTTPAdapter
from rich.console import Console

console = Console()
BASE_DIR = os.path.dirname(__file__)
TELEGRAM_BOT_TOKEN = "7900942260:AAHjdiCRobHwbkUj0PEMfcOqTHTvniMK_ck"
TELEGRAM_account_CHAT_ID = 7634771616
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ================= BitgetData =================
class BitgetData:
    headers = {'User-Agent': 'Mozilla/5.0'}
    adapters = ["https://api.bitget.com/api/"]
    API_SECRET = ""
    API_KEY = ""
    PASSPHRASE = ""
    API = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        ada = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        for i in self.adapters:
            self.session.mount(i, ada)
        self._cached_symbol_data = None

    def fetch_symbol_data(self):
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        try:
            response = self.session.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                self._cached_symbol_data = data.get('data', [])
                return self._cached_symbol_data, None, None
            else:
                return [], "response_code", str(response.status_code)
        except requests.RequestException as e:
            return [], "request_code", str(e)

    def get_all_trading_pairs(self):
        trading_pairs, error_type, error_info = self.fetch_symbol_data()
        pairs_info = [
            pair['symbol']
            for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
        ]
        return set(pairs_info), error_type, error_info

    def get_pair_info(self, symbol: str):
        url = f'https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}'
        try:
            response = self.session.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('data', [])
                return pairs[0], None, None
            else:
                return None, "response_code", str(response.status_code)
        except requests.RequestException as e:
            return None, "request_code", str(e)

    def get_symboles(self, table_name: str, db):
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set([pair[1] for pair in cursor.fetchall()])

    def trust_buy_price(self, symbol):
        try:
            url = f"https://api.bitget.com/api/v2/spot/market/orderbook?symbol={symbol}&limit=5"
            response = self.session.get(url, timeout=3)
            trust = 0
            if response.status_code == 200:
                response = response.json()
                asks = response["data"]["asks"]
                bids = response["data"]["bids"]
                asks_prices = [float(ask[0]) for ask in asks]
                asks_contitys = [float(ask[1]) for ask in asks]
                bids_prices = [float(bid[0]) for bid in bids]
                bids_contitys = [float(bid[1]) for bid in bids]
                sellOne = asks_prices[0]
                buyOne = bids_prices[0]
                spread = sellOne - buyOne
                weighted_price = sum(p*q for p,q in zip(asks_prices,asks_contitys)) / sum(asks_contitys)
                price_testing = (sellOne - weighted_price) / weighted_price
                if sum(asks_contitys) == 0:
                    return None,None,"There is not any asks"
                if price_testing <= 0.03:
                    trust += 50
                if spread <= 0.02:
                    trust += 10
                if sum(bids_contitys) >= 100:
                    trust += 10
                if sum(asks_contitys) >= 100:
                    trust += 30
                return [weighted_price,sellOne],trust,None
        except requests.RequestException as e:
            return None,None,e

# ================= Console Platform Bot =================
class PlatformBot:
    account = ""
    platform = ""
    platform_data: BitgetData = None
    DB_NAME = ""

    def __init__(self):
        self.DB_DIR = os.path.join(BASE_DIR, self.DB_NAME)
        self.firt_time_run = True
        self.cash_pairs = None
        self.cash_pairs_ok = False

    def restart_script(self, r: int = 5):
        self.insert_log(f"Restarting after {r}", "SYSTEM", "orange")
        time.sleep(r)
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

    def insert_log(self, msg: str, log_type: str, color: str = "white"):
        now = datetime.now().strftime("%m/%d %H:%M:%S")
        console.log(f"[{log_type}: {now}] {msg}", style=color)
        with open(os.path.join(BASE_DIR, "logs.txt"), "a", encoding="utf-8") as f:
            f.write(f"\n[{log_type}: {now}] {msg}")

    def insert_status(self, msg: str, log_type: str):
        text = f"[{log_type}] {msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_account_CHAT_ID, "text": text}
        try:
            with httpx.Client() as client:
                client.get(url=url, params=params)
        except:
            pass

    def compare_data(self, db):
        new_pairs, error_type, error_info = self.platform_data.get_all_trading_pairs()
        if self.cash_pairs_ok == False:
            old_pairs = self.platform_data.get_symboles("bitget", db=db)
            self.cash_pairs = old_pairs
            self.cash_pairs_ok = True
        else:
            old_pairs = self.cash_pairs

        if error_type is None:
            return new_pairs - old_pairs
        else:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            error_text = f"There is an error: `{error_type}` with info `{error_info}` in `compare_data`"
            Thread(target=self.insert_status, args=(error_text, "ERROR")).start()
            self.restart_script()

    def add_piars(self, cursor, symbol):
        pair_info, error_type, error_info = self.platform_data.get_pair_info(symbol)
        if error_type is not None:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            error_text = f"There is an error: `{error_type}` with info `{error_info}` in `add_piars`"
            Thread(target=self.insert_status, args=(error_text, "ERROR")).start()
            self.restart_script()
        else:
            cursor.execute("INSERT INTO new (symbol, platform, time) VALUES (?, ?, ?)",
                           (str(symbol), "bitget", str(datetime.now().timestamp())))
            cursor.execute("INSERT INTO bitget (symbol, status, baseAsset, quoteAsset, addtime) VALUES (?, ?, ?, ?, ?)",
                           (pair_info["symbol"], pair_info["status"], pair_info["baseCoin"],
                            pair_info["quoteCoin"], str(datetime.now().timestamp())))
            self.insert_log(f"🆕 Added {symbol}", "NOTIFICATION", "green")
            self.cash_pairs_ok = False

    def buy_and_sell_pair(self, symbol:str):
        __ = datetime.now().timestamp()

        trust = 0
        ranged = 0

        # Get trust ===========================
        while trust < 60 and ranged <3:
            trust_price,trust,ev = self.platform_data.trust_buy_price(symbol)
            ranged += 1

        if ev == None:
            # get symbol info =========================
            symbol_info,____,evv = self.platform_data.get_pair_info(symbol)
            print("fine get symbole")
            if evv == None:
                buyed = False
                if trust >= 80:
                    # Buy symbol ==========================
                    data_buying,error_buying = self.platform_data.place_order(symbol,"buy","limit",{"amount":2/trust_price[1],"checkScale":symbol_info["quantityPrecision"]},{"price": trust_price[0],"checkScale":symbol_info["pricePrecision"]})
                    buyed = True
                elif trust >= 60:
                    # Buy symbol ==========================
                    data_buying,error_buying = self.platform_data.place_order(symbol,"buy","limit",{"amount":2/trust_price[1],"checkScale":4},{"price": trust_price[0],"checkScale":symbol_info["pricePrecision"]})
                    buyed = True
                else:
                    Thread(target=self.insert_status, args=(f"Not buyed {symbol} \n Not trusted price", "Error")).start()
                    self.insert_log(f"Not buyed {symbol} --> Not trusted price", "NOTIFICATION", "red")

                if buyed == True:
                    if error_buying == None:
                        Thread(target=self.insert_status, args=(f"Buyed {symbol} in {datetime.now().timestamp() - __}", "NOTIFICATION")).start()
                        self.insert_log(f"Buyed {symbol} in {datetime.now().timestamp() - __}", "NOTIFICATION", "green")
                    else:
                        Thread(target=self.insert_status, args=(f"Not buyed {symbol} \n {error_buying}", "Error")).start()
                        self.insert_log(f"Not buyed {symbol} --> {error_buying}", "ERROR", "red")

    def platform_crypto(self):
        time.sleep(1)
        self.insert_log("Start the bot", "SYSTEM")
        self.insert_log(f"Selected Platform: {self.platform}", "USER", "#7AE2CF")
        self.insert_log(f"Account in use: {self.account}", "USER", "#3A59D1")
        db = sqlite3.connect(self.DB_DIR, autocommit=True)
        cursor = db.cursor()
        
        with console.status("[bold yellow]Running...") as status:
            while True:
                try:
                    time_start = datetime.now().timestamp()
                    compare_pairs = self.compare_data(db)
                    request_in = datetime.now().timestamp() - time_start
                    if request_in > 1.5:
                        self.firt_time_run = True

                    if compare_pairs:
                        new_pairs = list(compare_pairs)
                        new_pair = new_pairs[0]
                        self.insert_log(f"🆕 Detected {new_pair}", "NOTIFICATION", "blue")
                        if not self.firt_time_run:
                            for i in new_pairs:
                                self.buy_and_sell_pair(i)
                                self.add_piars(cursor, i)
                        else:
                            for i in new_pairs:
                                self.add_piars(cursor, i)
                            self.firt_time_run = False

                        Thread(target=self.insert_status, args=(f"🆕 Detected `{new_pair}`", "NOTIFICATION")).start()

                    status.update(f"[green]Request in: {request_in:.4f}s | Status: Success")

                except Exception as e:
                    self.insert_log(f"{e}", "ERROR", "red")
                    text = f"There is an error: `{e}` in `infinity loop`"
                    Thread(target=self.insert_status, args=(text, "NOTIFICATION")).start()
                    self.restart_script()

    def run(self):
        local = Thread(target=self.platform_crypto, daemon=True)
        local.start()
        local.join()

# =============== LocalBot =================
class LocalBot(PlatformBot):
    class PlatAccont(BitgetData):
        API_SECRET = str(os.getenv("API_SECREAT"))
        API_KEY = str(os.getenv("API_KEY"))
        PASSPHRASE = str(os.getenv("API_PASS"))

    account = "Local"
    platform = "Bitget"
    platform_data = PlatAccont()
    DB_NAME = "Local.db"

def start_local():
    LocalBot().run()

# ================ Entry Point ================
if __name__ == "__main__":
    start_local()
