import jwt
import time
import threading
import json
import sys
from time import sleep
import tkinter as tk
from tkinter import font as tkfont
import paho.mqtt.client as mqtt
from gpiozero import LED
led = LED(12)
SECRET_KEY = os.getenv("jwt_secret")
mqttbrokerip = os.getenv("mqttbrokerip")
mqttbrokerport = int(os.getenv("mqttbrokerport", 1883))
room_id = os.getenv("room_id")

tkinter_root = None
notification_window = None

def create_tkinter_app():
    global tkinter_root
    tkinter_root = tk.Tk()
    tkinter_root.withdraw()
    tkinter_root.mainloop()

def show_notification(message, duration=3, color="blue"):
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

def verify_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except Exception:
        return None

def generate_mqtt_password():
    payload = {"exp": time.time() + 10}  # token 10 sn geçerli
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# --- MQTT Callbacks ---
client = mqtt.Client()

def save_ip():
    try:
        topic = f"v1/{room_id}/saveip"
        payload = {"ip": "dynamic_ip_or_info"}  # Burayı kendi IP bilgisini alacak şekilde değiştir
        client.publish(topic, json.dumps(payload))
        print(f"[SAVEIP] MQTT publish -> {topic}")
    except Exception as e:
        print(f"[SAVEIP] Hata: {e}")

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Bağlandı, rc =", rc)
    # Her bağlantıda subscribe ve save_ip yapılır
    client.subscribe(f"v1/{room_id}/opendoor")
    print(f"[MQTT] Abone olunan topic: v1/{room_id}/opendoor")
    save_ip()

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnect oldu, rc={rc}")
    if rc != 0:
        print("[MQTT] Tekrar bağlanılıyor...")
        reconnect()

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
                show_notification("Kilit Açık!", duration=5, color='green')
                sleep(5)
                led.off()
            else:
                print("[OPENDOOR] Geçersiz token.")
        except Exception as e:
            print("[OPENDOOR] Hata:", e)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

def reconnect():
    while True:
        try:
            token = generate_mqtt_password()
            client.username_pw_set(f"{room_id}", token)
            client.reconnect()  # reconnect
            print(f"[MQTT] Reconnect başarılı, yeni token: {token}")
            break
        except Exception as e:
            print(f"[MQTT] Reconnect başarısız: {e}, 3 sn sonra tekrar denenecek...")
            time.sleep(3)

# --- Main ---
if __name__ == "__main__":
    try:
        # Tkinter thread
        tkinter_thread = threading.Thread(target=create_tkinter_app, daemon=True)
        tkinter_thread.start()

        # İlk bağlanma
        while True:
            try:
                token = generate_mqtt_password()
                client.username_pw_set(f"{room_id}", token)
                client.connect(mqttbrokerip, mqttbrokerport, 60)
                client.loop_start()  # arka planda çalışacak
                print(f"[MQTT] Bağlanıldı, token: {token}")
                break
            except Exception as e:
                print(f"[MQTT] Bağlantı başarısız: {e}, 3 sn sonra tekrar...")
                time.sleep(3)

        # Ana thread boşta kalacak
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C basıldı, çıkılıyor...")
    finally:
        try:
            client.disconnect()
        except:
            pass
        sys.exit(0)
