import speedtest

def get_internet_speed():
    st = speedtest.Speedtest()
    st.get_best_server()  # يختار أقرب سيرفر
    download = st.download() / 1_000_000  # تحويل من bits إلى Megabits
    upload = st.upload() / 1_000_000
    down, up = round(download, 2), round(upload, 2)
    return down, up

# مثال استخدام:
