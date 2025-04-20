import os
import sqlite3
from threading import Thread
from flask import Flask,render_template
from dotenv import load_dotenv
from asgiref.wsgi import WsgiToAsgi
from datetime import datetime
import get_pair,uvicorn
from bitget import *
import sqlite3,time
import tkinter as tk

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

# work functions ===================================================================================================
def bitget_crypto(): # ===> To compare the piars of bitget
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            time_start = datetime.now().timestamp()
            new_pairs = get_all_trading_pairs()
            old_pairs = get_pair.get_symboles(g="bitget",db=db)
            if new_pairs != [] and new_pairs != None:
                compare_pairs = new_pairs - old_pairs
                request_in = datetime.now().timestamp() - time_start
            else:
                compare_pairs = None 

            if compare_pairs:
                for f in compare_pairs:
                    cursor.execute( "INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f) , "bitget",str(datetime.now().timestamp())) )
                    pair_info = get_pair_info(f)
                    cursor.execute("INSERT INTO bitget (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseCoin"]),str(pair_info["quoteCoin"]),str(datetime.now().timestamp())))
                    new_listbox.insert(tk.END, f"🆕 {f} Aeded in: {datetime.now().strftime("%m/%d %H:%M:%S")}")
                db.commit()

            platform_status_speed.config(text=f"Request in: {request_in}S",fg="green" if request_in <= 1 else "orange")
            platform_status.config(text="Platform Status: Seccess",fg="green")
            time.sleep(0.5)

        except Exception as e:
            platform_status.config(text=f"Platform Status: error",fg="red")
            platform_status_speed.config(text=f"Request in: Error !!",fg="red")
            notif_label.config(text=f"Status error Error !!",fg="red")
            new_listbox.config(fg="red")
            new_listbox.insert(tk.END, e)
            time.sleep(5)

# Auther functions ======================================================================================================


# setunges branch ===================================================================================================
def main():

    # GUI start ---------------------------------------------------------------
    root = tk.Tk()
    root.title("status window for Bitget")
    root.geometry("400x300")
    root.configure(bg="#f0f0f0")
    global platform_status,notif_label,platform_status_speed,new_listbox

    platform_status = tk.Label(root, text="Platform Status: ---", font=("Arial", 14), bg="#f0f0f0")
    platform_status.pack(pady=5)

    platform_status_speed = tk.Label(root, text="Request in: ---", font=("Arial", 14), bg="#f0f0f0")
    platform_status_speed.pack(pady=5)

    notif_label = tk.Label(root, text="New pairs:", font=("Arial", 14), bg="#f0f0f0")
    notif_label.pack(pady=5)

    new_listbox = tk.Listbox(root, font=("Arial", 12), fg="green", height=10)
    new_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    root.mainloop()

    


if __name__ == "__main__":
    #gg = Thread(target=flask_start,daemon=True) # to start binanse
    #gg.start()

    # platform start ---------------------------------------------------------------
    print("Now bitget it work ========================================================================")
    Bitget = Thread(target=bitget_crypto,daemon=True) # to start bitget
    Bitget.start()

    main()