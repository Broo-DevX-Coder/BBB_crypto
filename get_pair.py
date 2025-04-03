import requests,os
# ===================================================================================
def get_symboles(g:str,db): # ===>  To get the symboles from DB 
    cursor = db.cursor()
    fd = []
    cursor.execute(f"SELECT * FROM {g}")
    fd = [pair[1] for pair in cursor.fetchall()]
    return set(fd)

def sand_TLG_msg(pla:str,smb:str):
    TOKEN = str(os.getenv("TLG_BOT"))
    CHAT_ID = str(os.getenv("TLG_ID"))
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    parames = {"chat_id":CHAT_ID,"text":f"A new pair uploaded in {pla} by symbol {smb}"}
    response = requests.get(url=url,params=parames)