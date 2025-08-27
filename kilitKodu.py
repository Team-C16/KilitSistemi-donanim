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
import threading
# GPIO Pin 12'yi LED olarak tanımlıyoruz
led = LED(12)  # GPIO Pin 12

# Tkinter importları
import tkinter as tk
from tkinter import font as tkfont



# Flask uygulaması oluşturma
app = Flask(__name__)

# Secret key 
SECRET_KEY = "JWT_SECRET"

raspberryNodeip = 'https://pve.izu.edu.tr/kilitSistemi'
 
room_id = 1


# Tkinter uygulama referansları
tkinter_root = None
notification_window = None

def create_tkinter_app():
    """Tkinter ana döngüsünü başlatan fonksiyon."""
    global tkinter_root
    tkinter_root = tk.Tk()
    tkinter_root.withdraw() # Ana pencereyi gizle
    tkinter_root.mainloop()

def show_notification(message, duration=3, color="blue"):
    """
    Ekranın sağ altında şeffaf ve çerçevesiz bir bildirim penceresi gösterir.
    Bu fonksiyonu Flask thread'inden güvenli bir şekilde çağırmak için after() metodu kullanılır.
    """
    def _show():
        global notification_window
        
        if notification_window and notification_window.winfo_exists():
            notification_window.destroy()
        
        notification_window = tk.Toplevel(tkinter_root)
        
        notification_window.overrideredirect(True)
        notification_window.wm_attributes("-topmost", True)
        # SİYAH ARKA PLAN YAPILDI
        notification_window.config(bg='white') 
        
        label = tk.Label(
            notification_window,
            text=message,
            font=tkfont.Font(family="Helvetica", size=40, weight="bold"),
            fg=color,
            bg='white'
        )
        label.pack(padx=20, pady=10)
        
        notification_window.update_idletasks()
        width = notification_window.winfo_width()
        height = notification_window.winfo_height()
        screen_width = notification_window.winfo_screenwidth()
        screen_height = notification_window.winfo_screenheight()
        x = 20
        y = screen_height - height - 200
        
        notification_window.geometry(f'+{x}+{y}')
        
        if duration > 0:
            notification_window.after(int(duration * 1000), notification_window.destroy)

    if tkinter_root and tkinter_root.winfo_exists():
        tkinter_root.after(0, _show)
        
def hide_notification():
    """Açık olan bildirim penceresini kapatır."""
    def _hide():
        global notification_window
        if notification_window and notification_window.winfo_exists():
            notification_window.destroy()
            
    if tkinter_root and tkinter_root.winfo_exists():
        tkinter_root.after(0, _hide)

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
    url = f"{raspberryNodeip}/saveIPForRaspberry"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": {room_id}, "jwtToken": "{encoded_jwt}", "ip": "{local_ip}"}}'
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
            
            print("TESTTTTTTT")
            show_notification("Kilit Açık!", duration=10, color='green')
            sleep(10)
            led.off()
            return jsonify({"message": "JWT is valid, LED is ON!"}), 200
        else:
            return jsonify({"message": "Invalid or expired JWT"}), 401
    else:
        return jsonify({"message": "No JWT provided"}), 400

if __name__ == '__main__':
    show_notification("Kilit Açık!", duration=10, color='green')
    time.sleep(10)
    # HTTP sunucusunu 80 portunda başlatıyoruz
    tkinter_thread = threading.Thread(target=create_tkinter_app)
    tkinter_thread.start()
    app.run(host='0.0.0.0', port=80)  # 80 portunu dinliyor
