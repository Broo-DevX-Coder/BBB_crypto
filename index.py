import sqlite3,time,os
from datetime import datetime
from threading import Thread
import binance,bitget
from datetime import datetime
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route("/viewer",methods=["GET","HEAD"])
def viewer():
    return "hellow viewer",200

# def branch ===================================================================================================

def get_symboles(g:str,db): # ===>  To get the symboles from DB 
    cursor = db.cursor()
    fd = []
    cursor.execute(f"SELECT * FROM {g}")
    fd = [pair[1] for pair in cursor.fetchall()]
    return set(fd)


def binance_crypto(): # ===> To compare the piars of binance
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            new_pairs = binance.get_usdt_pairs()
            old_pairs = get_symboles(g="binance",db=db)
            compare_pairs = new_pairs - old_pairs
            print("bitget")
            if compare_pairs:
                print(f"new pair detected{compare_pairs}")
                for f in compare_pairs:
                    cursor.execute("INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f),"binance",str(datetime.now().timestamp())))
                    pair_info = binance.get_pair_info(f)
                    cursor.execute("INSERT INTO binance (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseAsset"]),str(pair_info["quoteAsset"]),str(datetime.now().timestamp())))
                    db.commit()
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(10)


def bitget_crypto(): # ===> To compare the piars of bitget
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            new_pairs = bitget.get_all_trading_pairs()
            old_pairs = get_symboles(g="bitget",db=db)
            compare_pairs = new_pairs - old_pairs
            print("bitget")
            if compare_pairs:
                print(f"new pair detected{compare_pairs}")
                for f in compare_pairs:
                    cursor.execute("INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f),"bitget",str(datetime.now().timestamp())))
                    pair_info = bitget.get_pair_info(f)
                    cursor.execute("INSERT INTO bitget (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseAsset"]),str(pair_info["quoteAsset"]),str(datetime.now().timestamp())))
                    db.commit()
            time.sleep(2)
        except Exception as e:
            print(e)
            time.sleep(10)

# setunges branch ===================================================================================================
def main():
    Binanse = Thread(target=binance_crypto) # to start binanse
    Binanse.start()
    Bitget = Thread(target=bitget_crypto) # to start bitget
    Bitget.start()
    flask_app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
if __name__ == "__main__":
    main()