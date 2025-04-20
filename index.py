import os
from threading import Thread
from flask import Flask,render_template
from dotenv import load_dotenv
from asgiref.wsgi import WsgiToAsgi
from datetime import datetime
import get_pair,uvicorn
import sqlite3,time
from datetime import datetime

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

from bitget import *

# عناصر الواجهة العامة
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
        Thread(target=self.start_bitget_loop, daemon=True).start()
        return self.window

    def start_bitget_loop(self):
        db = sqlite3.connect("Crypto.db")
        cursor = db.cursor()
        while True:
            try:
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

            except Exception as e:
                Clock.schedule_once(lambda dt: self.window.update_status("error", "red"), 0)
                Clock.schedule_once(lambda dt: self.window.update_speed("Error !!", "red"), 0)
                Clock.schedule_once(lambda dt: self.window.add_pair(str(e), "red"), 0)
                time.sleep(10)


# main ===================================================================================================
load_dotenv("./.env")
flask_app = Flask(__name__)

# flask functions ===================================================================================================
def flask_start():
    asgi_app = WsgiToAsgi(flask_app)
    uvicorn.run(asgi_app,host="127.0.0.1",port=int(os.getenv("PORT",5000)))

@flask_app.route("/viewer",methods=["GET","HEAD"])
def viewer():
    return "hellow viewer",200

@flask_app.route("/",methods=["GET","HEAD"])
def front():
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM new")
    new = cursor.fetchall()
    db.close()

    return render_template("index.html",pairs=new)

@flask_app.template_filter("localtime")
def to_localtime(ts,strtime="%H:%M:%S %d/%m/%Y"):
    return datetime.fromtimestamp(float(ts)).strftime(str(strtime))



if __name__ == "__main__":
    
    flask_thread = Thread(target=flask_start, daemon=True)
    flask_thread.start()

    if str(os.getenv("PLATFORM")) == "bitget":
        print("Now bitget it work ========================================================================")

    BitgetApp().run()