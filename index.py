import os
import subprocess,sys
from threading import Thread
from dotenv import load_dotenv
from multiprocessing import Process
from datetime import datetime
import sqlite3,time
import requests
from multiprocessing import Process
import tkinter as tk

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
                pair = pairs[0]
                return pair, None, None
            else:
                pair = None
                return pair, "response_code", str(response.status_code)

        except requests.RequestException as e:
            pair = None
            return pair, "request_code", str(e)

    def get_symboles(self, table_name: str, db):
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set([pair[1] for pair in cursor.fetchall()])




class BitgetBot:
    API = ""
    SECREAT = ""
    accont = ""
    platform = ""
    platform_data = None

    # program functions =============================================================================================================================
    def __init__(self):

        self.BASE_DIR = os.path.dirname(__file__)
        self.DB_DIR = os.path.join(self.BASE_DIR,"Crypto.db")

        self.root = tk.Tk()
        self.root.title(f"Status Window -{self.accont}- -{self.platform}-")
        self.root.geometry("600x300")
        self.root.resizable(True, False)
        self.root.configure(bg="#f0f0f0")

        self.platform_status = tk.Label(self.root, text="Platform Status: ---", font=("Arial", 14), bg="#f0f0f0")
        self.platform_status.pack(pady=5)

        self.platform_status_speed = tk.Label(self.root, text="Request in: ---", font=("Arial", 14), bg="#f0f0f0")
        self.platform_status_speed.pack(pady=5)

        self.new_listbox = tk.Listbox(self.root, font=("Arial", 12), fg="green", height=10)
        self.new_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def restart_script(self, r:int=5):
        self.insert_log(f"Restarting after {r}", "SYSTEM", "orange")
        time.sleep(r)
        self.root.quit()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()

    # loges functions =============================================================================================================================
    def insert_log(self, msg, log_type:str, color="black"): # To insert a list item by parmes
        now = datetime.now().strftime("%m/%d %H:%M:%S")
        self.new_listbox.insert(0, f"[{log_type}: {now}] {msg}")
        self.new_listbox.itemconfig(0, {'fg': color})


    # dtat & platform functions ================================================================================================== 
    def compire_data(self,db):  # this for get pairs from platform and compier them and return the new pair
        new_pairs, error_type, error_info = self.platform_data.get_all_trading_pairs()
        old_pairs = self.platform_data.get_symboles("bitget", db=db)

        if error_type is None:
            compare_pairs = new_pairs - old_pairs
        else:
            self.insert_log(f"TYPE: {error_type}", "ERROR", "red")
            self.insert_log(f"INFO: {error_info}", "ERROR", "red")
            self.restart_script()

        return compare_pairs

    def add_piars(self,cursor,f):
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

    def buy_and_sell_pair(self,symbol):
        pass



    # ============================================================================================
    def platform_crypto(self):
        time.sleep(1)
        self.insert_log("Start the bot", "SYSTEM")
        self.insert_log(f"Shosed Platform> {self.platform}.", "USER", "#7AE2CF")
        self.insert_log(f"Accont worked> {self.accont}", "USER", "#3A59D1")

        db = sqlite3.connect(self.DB_DIR)
        cursor = db.cursor()

        while True:
            try:
                time_start = datetime.now().timestamp()
                compare_pairs = self.compire_data(db)
                request_in = datetime.now().timestamp() - time_start
                

                if compare_pairs:
                    new_pair = list(compare_pairs)[0]
                    self.insert_log(f"🆕 Detected {new_pair}","NOTIFICATION","blue")
                    self.add_piars(cursor,new_pair)
                    db.commit()

                self.platform_status_speed.config(text=f"Request in: {request_in:.4f}s", fg="green" if request_in <= 1 else "orange")
                self.platform_status.config(text="Platform Status: Success", fg="green")

            except Exception as e:
                self.platform_status.config(text="Platform Status: Error", fg="red")
                self.platform_status_speed.config(text="Request in: Error !!", fg="red")
                self.insert_log(f"Error> {e}", "ERROR", "red")
                self.restart_script()

    def run(self,):
        local = Thread(target=self.platform_crypto, daemon=True)
        local.start()
        self.root.mainloop()


class LocalBot(BitgetBot):
    accont = "Local"
    platform = "Bitget"
    platform_data = BitgetData()

"""
class PersonnelBot(BitgetBot):
    accont = "Personnel"
    platform = "Bitget"
    platform_data = BitgetData()

    def restart_script(self, r:int=5):
        self.insert_log(f"Restarting after {r}", "SYSTEM", "orange")
        time.sleep(r)
        self.root.quit()

def start_personnel():
    PersonnelBot().run()
"""

if __name__ == "__main__":
    #per = Process(target=start_personnel)
    #per.start()

    LocalBot().run()
