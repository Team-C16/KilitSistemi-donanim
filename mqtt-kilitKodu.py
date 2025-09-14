# encoding:utf-8

import jwt
import time
import socket
import threading
import json
import sys
from gpiozero import LED
from time import sleep

# Tkinter importları
import tkinter as tk
from tkinter import font as tkfont

import paho.mqtt.client as mqtt

# --- Konfigürasyon ---
SECRET_KEY = "DENEME"
mqttbrokerip = "192.168.1.130"     
mqttbrokerport = 1883
room_id = 2                        # Oda id

# GPIO Pin 12'yi LED olarak tanımlıyoruz
led = LED(12)  # GPIO Pin 12

# Tkinter referansları
tkinter_root = None
notification_window = None

def create_tkinter_app():
    """Tkinter ana döngüsünü başlatan fonksiyon."""
    global tkinter_root
    tkinter_root = tk.Tk()
    tkinter_root.withdraw()  # Ana pencereyi gizle
    tkinter_root.mainloop()

def show_notification(message, duration=3, color="blue"):
    """Bildirim penceresi gösterir."""
    def _show():
        global notification_window

        if notification_window and notification_window.winfo_exists():
            notification_window.destroy()

        notification_window = tk.Toplevel(tkinter_root)
        notification_window.overrideredirect(True)
        notification_window.wm_attributes("-topmost", True)
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

# --- JWT doğrulama ---
def verify_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except Exception:
        return None

# --- IP kaydet ---
def save_ip():
    try:
        topic = f"v1/{room_id}/saveip"
        client.publish(topic)
        print(f"[SAVEIP] MQTT publish -> {topic}")
    except Exception as e:
        print(f"[SAVEIP] Hata: {e}")

def generate_mqtt_password():
    payload = {
        "exp": time.time() + 30,   # 60 saniye geçerli olacak token
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- MQTT ---
client = mqtt.Client()
client.username_pw_set(f"{room_id}", generate_mqtt_password())

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Bağlandı, rc =", rc)
    client.subscribe(f"v1/{room_id}/opendoor")
    print(f"[MQTT] Abone olunan topic: v1/{room_id}/opendoor")
    # Bağlanınca IP bilgisini MQTT ile gönder
    save_ip()

def on_message(client, userdata, msg):
    print(f"[MQTT] Mesaj geldi: {msg.topic} -> {msg.payload}")
    if msg.topic.endswith("/opendoor"):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload) if payload.startswith("{") else {"token": payload}
            token = data.get("jwt") or data.get("token")
            if not token:
                print("[OPENDOOR] Token yok")
                return

            if verify_jwt(token):
                print("[OPENDOOR] Token geçerli, kapı açılıyor.")
                led.on()
                show_notification("Kilit Açık!", duration=10, color='green')
                sleep(10)
                led.off()
            else:
                print("[OPENDOOR] Geçersiz token.")
        except Exception as e:
            print("[OPENDOOR] Hata:", e)

client.on_connect = on_connect
client.on_message = on_message



# --- Main ---
if __name__ == "__main__":
    try:
        # Tkinter thread
        tkinter_thread = threading.Thread(target=create_tkinter_app, daemon=True)
        tkinter_thread.start()

        client.connect(mqttbrokerip, mqttbrokerport, 60)
        
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C basıldı, çıkılıyor...")
    finally:
        try:
            led.off()
            client.disconnect()
        except:
            pass
        sys.exit(0)
