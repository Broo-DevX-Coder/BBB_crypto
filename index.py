import os, subprocess, sys, sqlite3, time, requests, httpx
from threading import Thread
from datetime import datetime
from rich.console import Console

# Configuration
BASE_DIR = os.path.dirname(__file__)
PSQLDB = os.path.join(BASE_DIR, "PSQL.db")
TELEGRAM_BOT_TOKEN = "7900942260:AAHjdiCRobHwbkUj0PEMfcOqTHTvniMK_ck"
TELEGRAM_account_CHAT_ID = 7634771616
console = Console()

# ===================================================================
# Class to fetch data from Bitget ===================================
class BitgetData:
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._cached_symbol_data = None

    def fetch_symbol_data(self):
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        try:
            response = self.session.get(url, headers=self.headers)
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
            response = self.session.get(url, headers=self.headers)
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


# ===================================================================
# Main Bot Console Version ==========================================
class PlatformBot:
    API = ""
    SECREAT = ""
    account = ""
    platform = ""
    platform_data = None
    DB_NAME = ""

    def __init__(self):
        self.DB_DIR = os.path.join(BASE_DIR, self.DB_NAME)
        self.first_time_run = True

    def insert_log(self, msg, log_type, color="cyan"):
        console.log(f"[{color}][{log_type}: {datetime.now().strftime('%m/%d %H:%M:%S')}]{msg}")

    def insert_status(self, msg, log_type):
        text = f"[{log_type}] {msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_account_CHAT_ID, "text": text}
        try:
            with httpx.Client() as client:
                client.get(url=url, params=params)
        except:
            pass

    def restart_script(self, r: int = 5):
        self.insert_log(f"Restarting after {r} seconds", "SYSTEM", "orange")
        time.sleep(r)
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()

    def compare_data(self, db):
        new_pairs, error_type, error_info = self.platform_data.get_all_trading_pairs()
        old_pairs = self.platform_data.get_symboles("bitget", db=db)

        if error_type is None:
            return new_pairs - old_pairs
        else:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            error_text = f"There is an error: `{error_type}` with info `{error_info}` in `compare_data`"
            Thread(target=self.insert_status, args=(error_text, "ERROR")).start()
            self.restart_script()

    def add_pairs(self, cursor, symbol):
        pair_info, error_type, error_info = self.platform_data.get_pair_info(symbol)
        if error_type is not None:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            error_text = f"There is an error: `{error_type}` with info `{error_info}` in `add_pairs`"
            Thread(target=self.insert_status, args=(error_text, "ERROR")).start()
            self.restart_script()
        else:
            cursor.execute("INSERT INTO new (symbol, platform, time) VALUES (?, ?, ?)",
                           (str(symbol), "bitget", str(datetime.now().timestamp())))
            cursor.execute("INSERT INTO bitget (symbol, status, baseAsset, quoteAsset, addtime) VALUES (?, ?, ?, ?, ?)",
                           (pair_info["symbol"], pair_info["status"], pair_info["baseCoin"],
                            pair_info["quoteCoin"], str(datetime.now().timestamp())))
            self.insert_log(f"🆕 Added {symbol}", "NOTIFICATION", "green")

    def buy_and_sell_pair(self, symbol):
        pass  # Placeholder

    def platform_crypto(self):
        time.sleep(1)
        self.insert_log("Start the bot", "SYSTEM")
        self.insert_log(f"Selected Platform: {self.platform}", "USER", "#7AE2CF")
        self.insert_log(f"Account in use: {self.account}", "USER", "#3A59D1")

        db = sqlite3.connect(self.DB_DIR)
        cursor = db.cursor()

        with console.status("[bold yellow]Running...") as status:
            while True:
                try:
                    time_start = datetime.now().timestamp()
                    compare_pairs = self.compare_data(db)
                    request_in = datetime.now().timestamp() - time_start

                    if compare_pairs:
                        new_pair = list(compare_pairs)[0]
                        self.insert_log(f"🆕 Detected {new_pair}", "NOTIFICATION", "blue")

                        if not self.first_time_run:
                            self.buy_and_sell_pair(new_pair)
                        else:
                            self.first_time_run = False

                        text = f"🆕 Detected `{new_pair}`"
                        Thread(target=self.insert_status, args=(text, "NOTIFICATION")).start()
                        Thread(target=self.add_pairs, args=(cursor, new_pair)).start()
                        db.commit()

                    status.update(f"[green]Request in: {request_in:.4f}s | Status: Success")
                except Exception as e:
                    status.update("[bold red]❌ Error occurred!")
                    self.insert_log(f"Error> {e}", "ERROR", "red")
                    text = f"There is an error: `{e}` in `main loop`"
                    Thread(target=self.insert_status, args=(text, "NOTIFICATION")).start()
                    self.restart_script()

    def run(self):
        local = Thread(target=self.platform_crypto, daemon=True)
        local.start()
        local.join()


# ===================================================================
# Local bot configuration
class LocalBot(PlatformBot):
    account = "Local"
    platform = "Bitget"
    platform_data = BitgetData()
    DB_NAME = "Local.db"


if __name__ == "__main__":
    LocalBot().run()
