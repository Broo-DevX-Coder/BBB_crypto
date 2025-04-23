import os
import subprocess,sys
from threading import Thread
from dotenv import load_dotenv
from datetime import datetime
import sqlite3,time
import httpx
from multiprocessing import Process
import tkinter as tk

class BitgetData:
    def __init__(self):
        self._cached_symbol_data = None

    def fetch_symbol_data(self):
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                self._cached_symbol_data = data.get('data', [])
                return self._cached_symbol_data, None, None
            else:
                self._cached_symbol_data = []
                return self._cached_symbol_data, "response_code", str(response.status_code)

        except httpx.RequestError as e:
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
        symbols, e, r = self.fetch_symbol_data()
        for pair in symbols:
            if pair['symbol'] == symbol:
                return pair, None, None
        return None, "Not_found", "This pair not found !!"

    def get_symboles(self, table_name: str, db):
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set([pair[1] for pair in cursor.fetchall()])




class BitgetBot:
    # =======================
    API = ""
    SECREAT = ""
    accont = ""

    def __init__(self):

        self.BASE_DIR = os.path.dirname(__file__)
        self.DB_DIR = os.path.join(self.BASE_DIR,"Crypto.db")
        
        self.data = BitgetData()
        self.root = tk.Tk()
        self.root.title("Status Window for Bitget")
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
        self.insert_log("Restarting", "orange")
        time.sleep(r)
        self.root.quit()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()

    def insert_log(self, msg, color="black"): # To insert a list item by parmes
        now = datetime.now().strftime("%m/%d %H:%M:%S")
        self.new_listbox.insert(0, f"[SYSTEM: {now}] {msg}")
        self.new_listbox.itemconfig(0, {'fg': color})

    def insert_notify(self, msg, color="blue"):
        now = datetime.now().strftime("%m/%d %H:%M:%S")
        self.new_listbox.insert(0, f"[NOTIFICATION: {now}] {msg}")
        self.new_listbox.itemconfig(0, {'fg': color})

    def compire_data(self,db):  # this for get pairs from platform and compier them and return the new pair
        new_pairs, error_type, error_info = self.data.get_all_trading_pairs()
        old_pairs = self.data.get_symboles("bitget", db=db)
        if error_type is None:
            compare_pairs = new_pairs - old_pairs
        else:
            self.restart_script()

        return compare_pairs

    def add_piars(self,cursor,f):
        self.insert_notify(f"🆕 Detected {f}")
        cursor.execute("INSERT INTO new (symbol, platform, time) VALUES (?, ?, ?)", 
                                       (str(f), "bitget", str(datetime.now().timestamp())))
        pair_info, gg, r = self.data.get_pair_info(f)
        cursor.execute("INSERT INTO bitget (symbol, status, baseAsset, quoteAsset, addtime) VALUES (?, ?, ?, ?, ?)", 
                                       (pair_info["symbol"], pair_info["status"], pair_info["baseCoin"], pair_info["quoteCoin"], str(datetime.now().timestamp())))
        self.insert_notify(f"🆕 Added {f}", "green")



    # ============================================================================================
    def bitget_crypto(self):
        time.sleep(1)
        self.insert_log("Start the bot")
        self.insert_log("Shosed Platform> Bitget", "#7AE2CF")
        self.insert_log(f"Accont worked> {self.accont}", "#3A59D1")

        db = sqlite3.connect(self.DB_DIR)
        cursor = db.cursor()

        while True:
            try:
                time_start = datetime.now().timestamp()
                compare_pairs = self.compire_data(db)
                request_in = datetime.now().timestamp() - time_start
                

                if compare_pairs:
                    new_pair = compare_pairs[0]
                    self.add_piars(self,cursor,new_pair)
                    db.commit()

                self.platform_status_speed.config(text=f"Request in: {request_in:.4f}s", fg="green" if request_in <= 1 else "orange")
                self.platform_status.config(text="Platform Status: Success", fg="green")

            except Exception as e:
                self.platform_status.config(text="Platform Status: Error", fg="red")
                self.platform_status_speed.config(text="Request in: Error !!", fg="red")
                self.insert_log(f"Error> {e}", "red")
                self.restart_script()

    def run(self,):
        local = Thread(target=self.bitget_crypto, daemon=True)
        local.start()
        self.root.mainloop()


class LocalBot(BitgetBot):
    accont = "Local"


if __name__ == "__main__":
    LocalBot().run()
