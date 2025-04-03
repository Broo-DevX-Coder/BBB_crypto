import os
from threading import Thread
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route("/viewer",methods=["GET","HEAD"])
def viewer():
    return "hellow viewer",200

# setunges branch ===================================================================================================
def main():

    if str(os.getenv("PLATFORM")) == "binance":
        import binance
        Binanse = Thread(target=binance.binance_crypto) # to start binanse
        Binanse.start()
    elif str(os.getenv("PLATFORM")) == "bitget":
        import bitget
        Bitget = Thread(target=bitget.bitget_crypto) # to start bitget
        Bitget.start()

    flask_app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
if __name__ == "__main__":
    main()