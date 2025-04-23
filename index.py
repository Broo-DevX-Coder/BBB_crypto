import os
import subprocess, sys
from threading import Thread
from dotenv import load_dotenv
from multiprocessing import Process
from datetime import datetime
import sqlite3, time
import requests
from rich.console import Console
from rich.status import Status

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
                self._cached_symbol_data = []
                return self._cached_symbol_data, "response_code", str(response.status_code)
        except requests.RequestException as e:
            self._cached_symbol_data = []
            return self._cached_symbol_data, "request_code", str(e)

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


class PlatformBot:
    API = ""
    SECREAT = ""
    accont = ""
    platform = ""
    platform_data = None
    DB = "Crypto.db"

    def __init__(self):
        self.BASE_DIR = os.path.dirname(__file__)
        self.DB_DIR = os.path.join(self.BASE_DIR, self.DB)
        self.console = Console()

    def restart_script(self, r: int = 5):
        self.insert_log(f"Restarting after {r} seconds", "SYSTEM", "orange")
        time.sleep(r)
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()

    def compire_data(self, db):
        new_pairs, error_type, error_info = self.platform_data.get_all_trading_pairs()
        old_pairs = self.platform_data.get_symboles("bitget", db=db)

        if error_type is None:
            return new_pairs - old_pairs
        else:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            self.restart_script()

    def add_piars(self, cursor, f):
        pair_info, error_type, error_info = self.platform_data.get_pair_info(f)
        if error_type is not None:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            self.restart_script()
        else:
            cursor.execute("INSERT INTO new (symbol, platform, time) VALUES (?, ?, ?)", 
                           (str(f), "bitget", str(datetime.now().timestamp())))
            cursor.execute("INSERT INTO bitget (symbol, status, baseAsset, quoteAsset, addtime) VALUES (?, ?, ?, ?, ?)", 
                           (pair_info["symbol"], pair_info["status"], pair_info["baseCoin"], pair_info["quoteCoin"], str(datetime.now().timestamp())))
            self.insert_log(f"🆕 Added {f}", "NOTIFICATION", "green")

    def insert_log(self,msg,log_type,color="cyan"):
        self.console.log(f"[{color}][{log_type}: {datetime.now().strftime("%d/%M/%Y %H:%m:%S")}]{msg}")

    def platform_crypto(self):
        time.sleep(1)
        self.insert_log(f"Start the bot", "SYSTEM", "bold cyan")
        self.insert_log(f"Chosen Platform > {self.platform}", "SYSTEM", "bold blue")
        self.insert_log(f"Account working > {self.accont}", "SYSTEM", "bold blue")

        

        db = sqlite3.connect(self.DB_DIR)
        cursor = db.cursor()

        with self.console.status("[bold yellow]Fetching trading pairs...") as status:
            while True:
                try:
                    time_start = datetime.now().timestamp()
                    compare_pairs = self.compire_data(db)
                    request_in = datetime.now().timestamp() - time_start

                    if compare_pairs:
                        new_pair = list(compare_pairs)[0]
                        self.insert_log(f"🆕 Detected {new_pair}", "NOTIFICATION", "green")
                        self.add_piars(cursor, new_pair)
                        db.commit()


                    status.update(f"[green]Request completed in {request_in:.4f}s | Status: Success")


                except Exception as e:
                    status.update("[bold red]❌ Error occurred!")
                    self.insert_log(f"{e}", "ERROR", "red")
                    self.restart_script()

    def run(self):
        local = Thread(target=self.platform_crypto, daemon=True)
        local.start()
        local.join()


class LocalBot(PlatformBot):
    accont = "Local"
    platform = "Bitget"
    platform_data = BitgetData()


    def restart_script(self, r: int = 5):
        self.insert_log(f"Restarting after {r} seconds", "SYSTEM", "orange")
        time.sleep(r)
        sys.exit()

if __name__ == "__main__":

    LocalBot().run()
