from flask import Flask, request, jsonify
import jwt
import datetime
from gpiozero import LED
from time import sleep
# GPIO Pin 12'yi LED olarak tanımlıyoruz
led = LED(12)  # GPIO Pin 12

# Flask uygulaması oluşturma
app = Flask(__name__)

# Secret key (Bunu kendi secret key'inizle değiştirin)
SECRET_KEY = "{zRUm1BL(0S_ylR*/2RwmV]v*Yf!CD|_2O+9R9M7.XM~T#{f|k"

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
            sleep(10.0)
            led.off()
            return jsonify({"message": "JWT is valid, LED is ON!"}), 200
        else:
            return jsonify({"message": "Invalid or expired JWT"}), 401
    else:
        return jsonify({"message": "No JWT provided"}), 400

if __name__ == '__main__':
    # HTTP sunucusunu 80 portunda başlatıyoruz
    app.run(host='0.0.0.0', port=80)  # 80 portunu dinliyor
