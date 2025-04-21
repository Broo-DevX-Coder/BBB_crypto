import os
import sqlite3
import subprocess,sys
from threading import Thread
from dotenv import load_dotenv
from datetime import datetime
import get_pair
from bitget import *
import sqlite3,time
import tkinter as tk

# work functions ===================================================================================================
def bitget_crypto(): # ===> To compare the piars of bitget
    time.sleep(1)
    new_listbox.insert(0, f"[SYSTEM: {datetime.now().strftime("%m/%d %H:%M:%S")}] Start the bot ")
    new_listbox.itemconfig(0, {'fg': "black"})
    new_listbox.insert(0, f"[SYSTEM: {datetime.now().strftime("%m/%d %H:%M:%S")}] Shosed Platform> Bitget")
    new_listbox.itemconfig(0, {'fg':"#7AE2CF"})
    db = sqlite3.connect("Crypto.db")
    cursor = db.cursor()
    while True:
        try:
            time_start = datetime.now().timestamp()
            new_pairs,new_pairs_error_type,new_pairs_error_info = get_all_trading_pairs()
            old_pairs = get_pair.get_symboles(g="bitget",db=db)

            
            if new_pairs_error_type is None:
                compare_pairs = new_pairs - old_pairs
                request_in = datetime.now().timestamp() - time_start
            elif new_pairs_error_type == "response_code":    
                new_listbox.insert(0, f"[SYSTEM: {datetime.now().strftime("%m/%d %H:%M:%S")}] Restarting ")
                new_listbox.itemconfig(0, {'fg': "orange"}) 
                restart_script()
            elif new_pairs_error_type == "request_code":
                new_listbox.insert(0, f"[SYSTEM: {datetime.now().strftime("%m/%d %H:%M:%S")}] Restarting ")
                new_listbox.itemconfig(0, {'fg': "orange"})
                restart_script()

                

            if compare_pairs:
                for f in compare_pairs:
                    new_listbox.insert(0, f"[NOTIFICATION: {datetime.now().strftime("%m/%d %H:%M:%S")}] 🆕 Detected {f}")
                    new_listbox.itemconfig(0, {'fg': "blue"})
                    cursor.execute( "INSERT INTO new (symbol,platform,time) VALUES (?,?,?)", (str(f) , "bitget",str(datetime.now().timestamp())) )
                    pair_info,gg,r = get_pair_info(f)
                    cursor.execute("INSERT INTO bitget (symbol,status,baseAsset,quoteAsset,addtime) VALUES (?,?,?,?,?)", (str(pair_info["symbol"]),str(pair_info["status"]),str(pair_info["baseCoin"]),str(pair_info["quoteCoin"]),str(datetime.now().timestamp())))
                    new_listbox.insert(0, f"[NOTIFICATION: {datetime.now().strftime("%m/%d %H:%M:%S")}] 🆕 Aeded {f}")
                    new_listbox.itemconfig(0, {'fg': "green"})
                db.commit()

            platform_status_speed.config(text=f"Request in: {request_in}S",fg="green" if request_in <= 1 else "orange")
            platform_status.config(text="Platform Status: Seccess",fg="green")

        except Exception as e:
            platform_status.config(text=f"Platform Status: error",fg="red")
            platform_status_speed.config(text=f"Request in: Error !!",fg="red")
            new_listbox.insert(0, f"[SYSTEM: {datetime.now().strftime("%m/%d %H:%M:%S")}] Error>\n{e} ")
            new_listbox.itemconfig(0, {'fg': "red"})
            print(e)
            time.sleep(5)
            restart_script()

# Auther functions ======================================================================================================
def restart_script(r:int = 5):
    time.sleep(int(r))
    root.quit()
    subprocess.Popen([sys.executable]+sys.argv)
    sys.exit()

# setunges branch ===================================================================================================
def main():

    # GUI start ---------------------------------------------------------------
    global root,platform_status,platform_status_speed,new_listbox

    root = tk.Tk()
    root.title("status window for Bitget")
    root.geometry("600x300")
    root.resizable(False,False)
    root.configure(bg="#f0f0f0")

    platform_status = tk.Label(root, text="Platform Status: ---", font=("Arial", 14), bg="#f0f0f0")
    platform_status.pack(pady=5)

    platform_status_speed = tk.Label(root, text="Request in: ---", font=("Arial", 14), bg="#f0f0f0")
    platform_status_speed.pack(pady=5)

    new_listbox = tk.Listbox(root, font=("Arial", 12), fg="green", height=10)
    new_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    root.mainloop()

    


if __name__ == "__main__":

    # platform start ---------------------------------------------------------------
    Bitget = Thread(target=bitget_crypto,daemon=True) # to start bitget
    Bitget.start()

    main()