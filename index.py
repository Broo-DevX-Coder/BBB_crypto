from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineListItem, MDList
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivy.clock import Clock

import os, sys, time, sqlite3, subprocess
import requests
from threading import Thread
from datetime import datetime


class BitgetData:
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._cached_symbol_data = None

    def fetch_symbol_data(self):
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                self._cached_symbol_data = response.json().get('data', [])
                return self._cached_symbol_data, None, None
            else:
                return [], "response_code", str(response.status_code)
        except requests.RequestException as e:
            return [], "request_code", str(e)

    def get_all_trading_pairs(self):
        pairs, err_type, err_info = self.fetch_symbol_data()
        return {p['symbol'] for p in pairs if p['status'] == 'online' and p['quoteCoin'] == "USDT"}, err_type, err_info

    def get_pair_info(self, symbol: str):
        url = f'https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}'
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json().get('data', [])
                return data[0], None, None
            return None, "response_code", str(response.status_code)
        except requests.RequestException as e:
            return None, "request_code", str(e)

    def get_symboles(self, table_name: str, db):
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set(row[1] for row in cursor.fetchall())


class BitgetBot(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accont = "Local"
        self.platform = "Bitget"
        self.platform_data = BitgetData()
        self.DB = os.path.join(os.path.dirname(__file__), "Crypto.db")

        self.layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)

        self.toolbar = MDTopAppBar(title=f"{self.accont} | {self.platform}", pos_hint={"top": 1})
        self.layout.add_widget(self.toolbar)

        self.status_label = MDLabel(text="Platform Status: ---", halign="center", theme_text_color="Custom", text_color=(0, 0, 0, 1))
        self.speed_label = MDLabel(text="Request in: ---", halign="center", theme_text_color="Custom", text_color=(0, 0, 0, 1))

        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.speed_label)

        self.scroll = MDScrollView()
        self.msg_list = MDList()
        self.scroll.add_widget(self.msg_list)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

        Thread(target=self.platform_crypto, daemon=True).start()

    def get_color(self, log_type):
        colors = {
            "SYSTEM": (1, 1, 1, 1),
            "USER": (0, 0.5, 1, 1),
            "ERROR": (1, 0, 0, 1),
            "NOTIFICATION": (0, 1, 0, 1),
        }
        return colors.get(log_type, (1, 1, 1, 1))

    def insert_log(self, msg, log_type, color=None):
        now = datetime.now().strftime("%H:%M:%S")
        if color is None:
            color = self.get_color(log_type)

        def add_log_to_ui(dt):
            item = OneLineListItem(
                text=f"[{log_type} {now}] {msg}",
                theme_text_color="Custom",
                text_color=color
            )
            self.msg_list.add_widget(item)

        Clock.schedule_once(add_log_to_ui)

    def restart_script(self, r=5):
        self.insert_log(f"Restarting after {r}s", "SYSTEM", color=(1, 0.5, 0, 1))
        time.sleep(r)
        sys.exit()

    def compire_data(self, db):
        new_pairs, err_type, err_info = self.platform_data.get_all_trading_pairs()
        old_pairs = self.platform_data.get_symboles("bitget", db=db)
        if err_type is None:
            return new_pairs - old_pairs
        else:
            self.insert_log(f"TYPE: {err_type}", "ERROR")
            self.insert_log(f"INFO: {err_info}", "ERROR")
            self.restart_script()

    def add_piars(self, cursor, f):
        info, err_type, err_info = self.platform_data.get_pair_info(f)
        if err_type:
            self.insert_log(f"TYPE: {err_type}", "ERROR")
            self.insert_log(f"INFO: {err_info}", "ERROR")
            self.restart_script()
        else:
            timestamp = str(datetime.now().timestamp())
            cursor.execute("INSERT INTO new (symbol, platform, time) VALUES (?, ?, ?)", (f, "bitget", timestamp))
            cursor.execute("INSERT INTO bitget (symbol, status, baseAsset, quoteAsset, addtime) VALUES (?, ?, ?, ?, ?)",
                           (info["symbol"], info["status"], info["baseCoin"], info["quoteCoin"], timestamp))
            self.insert_log(f"🆕 Added {f}", "NOTIFICATION")

    def platform_crypto(self):
        with sqlite3.connect(self.DB) as db:
            cursor = db.cursor()

            self.insert_log("Bot started", "SYSTEM")
            self.insert_log(f"Using platform: {self.platform}", "USER")
            self.insert_log(f"Account: {self.accont}", "USER")

            while True:
                try:
                    start = datetime.now().timestamp()
                    pairs = self.compire_data(db)
                    elapsed = datetime.now().timestamp() - start

                    if pairs:
                        f = list(pairs)[0]
                        self.insert_log(f"🆕 Detected {f}", "NOTIFICATION", color=(0, 0, 1, 1))
                        self.add_piars(cursor, f)
                        db.commit()

                    self.status_label.text = "Platform Status: Success"
                    self.status_label.text_color = (0, 1, 0, 1)
                    self.speed_label.text = f"Request in: {elapsed:.4f}s"
                    self.speed_label.text_color = (0, 1, 0, 1) if elapsed <= 1 else (1, 0.5, 0, 1)

                except Exception as e:
                    self.status_label.text = "Platform Status: Error"
                    self.status_label.text_color = (1, 0, 0, 1)
                    self.speed_label.text = "Request in: Error"
                    self.speed_label.text_color = (1, 0, 0, 1)
                    self.insert_log(f"Error: {e}", "ERROR")
                    self.restart_script()


class MainApp(MDApp):
    def build(self):
        return BitgetBot()


if __name__ == '__main__':
    MainApp().run()
