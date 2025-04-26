# ===================================================================
import os, subprocess, sys, requests, sqlite3, time, httpx
from threading import Thread
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk

# Configuration and Paths ============================================
BASE_DIR = os.path.dirname(__file__)
PSQLDB = os.path.join(BASE_DIR, "PSQL.db")
TELEGRAM_BOT_TOKEN = "7900942260:AAHjdiCRobHwbkUj0PEMfcOqTHTvniMK_ck"
TELEGRAM_account_CHAT_ID = 7634771616

# ===================================================================
# Class to fetch data from Bitget ===================================
class BitgetData:
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._cached_symbol_data = None

    def fetch_symbol_data(self):
        # Request all available trading pairs
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
        # Get all USDT trading pairs that are online
        trading_pairs, error_type, error_info = self.fetch_symbol_data()
        pairs_info = [
            pair['symbol']
            for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
        ]
        return set(pairs_info), error_type, error_info

    def get_pair_info(self, symbol: str):
        # Get full information for a specific trading pair
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
        # Get all stored symbols from database
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set([pair[1] for pair in cursor.fetchall()])

# ===================================================================
# Main Platform + GUI Controller ====================================
class PlatformBot:
    API = ""
    SECREAT = ""
    account = ""
    platform = ""
    platform_data = None
    DB_NAME = ""

    def __init__(self):
        self.DB_DIR = os.path.join(BASE_DIR, self.DB_NAME)
        self.firt_time_run = True

        # Create GUI window
        self.root = tk.Tk()
        self.root.title(f"Status Window -{self.account}- -{self.platform}-")
        self.root.geometry("600x300")
        self.root.resizable(True, False)
        self.root.configure(bg="#f0f0f0")

        self.platform_status = tk.Label(self.root, text="Platform Status: ---", font=("Arial", 14), bg="#f0f0f0")
        self.platform_status.pack(pady=5)

        self.platform_status_speed = tk.Label(self.root, text="Request in: ---", font=("Arial", 14), bg="#f0f0f0")
        self.platform_status_speed.pack(pady=5)

        self.new_listbox = tk.Listbox(self.root, font=("Arial", 12), fg="green", height=10)
        self.new_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def restart_script(self, r: int = 5):
        # Restart the script after r seconds
        self.insert_log(f"Restarting after {r}", "SYSTEM", "orange")
        time.sleep(r)
        for i in self.apps:
            i.close()
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

    def insert_log(self, msg: str, log_type: str, color: str = "black"):
        # Insert message into the GUI log
        now = datetime.now().strftime("%m/%d %H:%M:%S")
        self.new_listbox.insert(0, f"[{log_type}: {now}] {msg}")
        self.new_listbox.itemconfig(0, {'fg': color})

    def insert_status(self, msg: str, log_type: str):
        # Send a Telegram message
        text = f"[{log_type}] {msg}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_account_CHAT_ID, "text": text}
        with httpx.Client() as client:
            client.get(url=url, params=params)

    def compare_data(self, db):
        # Compare new fetched pairs with those in the database
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

    def add_piars(self, cursor, symbol):
        # Add a newly detected pair to the database
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

    def buy_and_sell_pair(self, symbol):
        # Placeholder for Buy/Sell logic
        pass

    def platform_crypto(self):
        # Main bot logic loop
        time.sleep(1)
        self.insert_log("Start the bot", "SYSTEM")
        self.insert_log(f"Selected Platform: {self.platform}", "USER", "#7AE2CF")
        self.insert_log(f"Account in use: {self.account}", "USER", "#3A59D1")

        db = sqlite3.connect(self.DB_DIR, autocommit=True)
        cursor = db.cursor()

        while True:
            try:
                time_start = datetime.now().timestamp()
                compare_pairs = self.compare_data(db)
                request_in = datetime.now().timestamp() - time_start

                if compare_pairs:
                    new_pair = list(compare_pairs)[0]
                    self.insert_log(f"🆕 Detected {new_pair}", "NOTIFICATION", "blue")

                    if not self.firt_time_run:
                        self.buy_and_sell_pair(new_pair)
                    else:
                        self.firt_time_run = False

                    text = f"🆕 Detected `{new_pair}`"
                    Thread(target=self.insert_status, args=(text, "NOTIFICATION")).start()
                    Thread(target=self.add_piars, args=(cursor, new_pair)).start()

                self.platform_status_speed.config(text=f"Request in: {request_in:.4f}s",
                                                  fg="green" if request_in <= 1 else "orange")
                self.platform_status.config(text="Platform Status: Success", fg="green")

            except Exception as e:
                self.platform_status.config(text="Platform Status: Error", fg="red")
                self.platform_status_speed.config(text="Request in: Error !!", fg="red")
                self.insert_log(f"Error> {e}", "ERROR", "red")
                text = f"There is an error: `{e}` in `infinity loop`"
                Thread(target=self.insert_status, args=(text, "NOTIFICATION")).start()
                self.restart_script()

    def run(self):
        # Start the logic loop and GUI
        local = Thread(target=self.platform_crypto, daemon=True)
        local.start()
        self.root.mainloop()

# ===================================================================
# Example: A Local account config ===================================
class LocalBot(PlatformBot):
    account = "Local"
    platform = "Bitget"
    platform_data = BitgetData()
    DB_NAME = "Local.db"

def start_local():
    LocalBot().run()

# ===================================================================
# Entry point ========================================================
if __name__ == "__main__":
    start_local()