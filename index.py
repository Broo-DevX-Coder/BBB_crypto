import os
from threading import Thread
from datetime import datetime
import get_pair
import sqlite3, time
import socket

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

from bitget import *

# الواجهة
class StatusWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        self.platform_status = Label(text="Platform Status: ---", font_size=18)
        self.platform_status_speed = Label(text="Request in: ---", font_size=18)
        self.notif_label = Label(text="New pairs:", font_size=18)

        self.pair_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.pair_list_layout.bind(minimum_height=self.pair_list_layout.setter('height'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.pair_list_layout)

        self.add_widget(self.platform_status)
        self.add_widget(self.platform_status_speed)
        self.add_widget(self.notif_label)
        self.add_widget(self.scroll)

    def add_pair(self, text, color="00ff00"):
        label = Label(
            text=text,
            size_hint_y=None,
            height=30,
            color=(1, 0, 0, 1) if color == "red" else (0, 1, 0, 1)
        )
        self.pair_list_layout.add_widget(label)

    def update_status(self, text, color="green"):
        self.platform_status.text = f"Platform Status: {text}"
        self.platform_status.color = (0, 1, 0, 1) if color == "green" else (1, 0, 0, 1)

    def update_speed(self, text, color="green"):
        self.platform_status_speed.text = f"Request in: {text}"
        self.platform_status_speed.color = (0, 1, 0, 1) if color == "green" else (1, 0.5, 0, 1)


class BitgetApp(App):
    def build(self):
        self.window = StatusWindow()

        # تحقق من الاتصال في البداية
        if not self.check_internet():
            Clock.schedule_once(lambda dt: self.window.add_pair("There is not internet connection", "red"), 0)
            Clock.schedule_once(lambda dt: self.stop(), 5)
        else:
            Thread(target=self.start_bitget_loop, daemon=True).start()

        return self.window

    def check_internet(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error: 
            
            return False

    def start_bitget_loop(self):
        db = sqlite3.connect("Crypto.db")
        cursor = db.cursor()
        while True:
            try:
                # تحقق من الاتصال أثناء التشغيل
                if not self.check_internet():
                    Clock.schedule_once(lambda dt: self.window.add_pair("There is not internet connection", "red"), 0)
                    Clock.schedule_once(lambda dt: self.stop(), 5)
                    break  # أوقف اللوب بعد جدولة الإغلاق

                time_start = datetime.now().timestamp()
                new_pairs = get_all_trading_pairs()
                old_pairs = get_pair.get_symboles(g="bitget", db=db)

                if new_pairs:
                    compare_pairs = new_pairs - old_pairs
                    request_in = datetime.now().timestamp() - time_start
                else:
                    compare_pairs = None

                if compare_pairs:
                    for f in compare_pairs:
                        cursor.execute(
                            "INSERT INTO new (symbol,platform,time) VALUES (?,?,?)",
                            (str(f), "bitget", str(datetime.now().timestamp()))
                        )
                        pair_info = get_pair_info(f)
                        cursor.execute(
                            "INSERT INTO bitget (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)",
                            (
                                str(pair_info["symbol"]),
                                str(pair_info["status"]),
                                str(pair_info["baseCoin"]),
                                str(pair_info["quoteCoin"]),
                                str(datetime.now().timestamp())
                            )
                        )
                        Clock.schedule_once(lambda dt, msg=f: self.window.add_pair(f"🆕 {msg} Added in: {datetime.now().strftime('%m/%d %H:%M:%S')}"), 0)
                    db.commit()

                Clock.schedule_once(lambda dt: self.window.update_speed(f"{request_in:.2f}S", "green" if request_in <= 1 else "orange"), 0)
                Clock.schedule_once(lambda dt: self.window.update_status("Success", "green"), 0)
                time.sleep(0.5)

            except Exception as e:
                Clock.schedule_once(lambda dt: self.window.update_status("error", "red"), 0)
                Clock.schedule_once(lambda dt: self.window.update_speed("Error !!", "red"), 0)
                Clock.schedule_once(lambda dt: self.window.add_pair(str(e), "red"), 0)
                time.sleep(10)


if __name__ == "__main__":
    print("Now bitget it work ========================================================================")
    BitgetApp().run()
