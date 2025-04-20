# ===================================================================================
def get_symboles(g:str,db): # ===>  To get the symboles from DB 
    cursor = db.cursor()
    fd = []
    cursor.execute(f"SELECT * FROM {g}")
    fd = [pair[1] for pair in cursor.fetchall()]
    return set(fd)