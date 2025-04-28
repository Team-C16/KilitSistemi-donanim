# encoding:utf-8

from flask import Flask, request, jsonify
import jwt
import datetime
from gpiozero import LED
from time import sleep
import time
import subprocess
import socket
import requests
# GPIO Pin 12'yi LED olarak tanımlıyoruz
led = LED(12)  # GPIO Pin 12

# Flask uygulaması oluşturma
app = Flask(__name__)

# Secret key 
SECRET_KEY = "JWT_SECRET"
# JWT doğrulama fonksiyonu
def verify_jwt(token):
    try:
        # JWT'yi doğrula
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded  # JWT geçerliyse, çözümlenmiş payload'ı döner
    except jwt.ExpiredSignatureError:
        return None  # JWT süresi dolmuş
    except jwt.InvalidTokenError:
        return None  # Geçersiz JWT
        
def save_ip():
    print("Save ip called")
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 30  # 30 saniye içinde geçersiz olacak
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    print(local_ip)
    url = f"http://172.28.6.24:32002/saveIPForRaspberry"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": 1, "jwtToken": "{encoded_jwt}", "ip": "{local_ip}"}}'
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response
        else:
            print(f"API isteği başarısız oldu. IP Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")
    return None

print(save_ip())

# POST isteği dinleyen bir route
@app.route('/verify', methods=['POST'])
def verify_token():
    # POST isteğinden JWT'yi al
    data = request.json
    token = data.get("jwt")

    if token:
        # JWT'yi doğrula
        decoded = verify_jwt(token)
        if decoded:
            # JWT geçerli, sinyal gönder (LED'i aç)
            led.on()
            command = f'echo "KILIT AÇIK!" | osd_cat -p top -d 10 -c blue -i 10 -o 700 -f "-*-*-*-r-*--60-*-*-*-*-*-*-*"'
            subprocess.run(command, shell=True)
            led.off()
            return jsonify({"message": "JWT is valid, LED is ON!"}), 200
        else:
            return jsonify({"message": "Invalid or expired JWT"}), 401
    else:
        return jsonify({"message": "No JWT provided"}), 400

if __name__ == '__main__':
    # HTTP sunucusunu 80 portunda başlatıyoruz
    app.run(host='0.0.0.0', port=80)  # 80 portunu dinliyor
