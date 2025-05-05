#!/bin/bash

# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python و pip
sudo apt install -y python3-pip

# التأكد من وجود Tkinter (لـ GUI مثل Tkinter)
sudo apt install -y python3-tk

# تثبيت أدوات إضافية
sudo apt install -y git build-essential

# إنشاء مجلد المشروع
mkdir -p ~/bbb_crypto
cd ~/bbb_crypto

# إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate

# إنشاء ملف requirements.txt
cat > requirements.txt <<EOF
requests
httpx
python-dotenv
EOF

# تثبيت المتطلبات
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ تم إعداد السيرفر بنجاح!"
echo "📂 المشروع في: ~/bbb_crypto"
echo "💡 لتفعيل البيئة: source ~/bbb_crypto/venv/bin/activate"
