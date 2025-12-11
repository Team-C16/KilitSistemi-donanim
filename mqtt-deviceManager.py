import os
import time
import json
import sys
import subprocess
import jwt
import paho.mqtt.client as mqtt

MQTT_IP = os.getenv("mqttbrokerip")
MQTT_PORT = int(os.getenv("mqttbrokerport", 1883))
ROOM_ID = os.getenv("room_id")
SECRET_KEY = os.getenv("SECRET_KEY")
DESTINATION_DIR = os.getenv("DESTINATION_DIR")
SERVICE_QR = os.getenv("SERVICE_QR")
SERVICE_LOCK = os.getenv("SERVICE_LOCK")
SERVICE_FINGER = os.getenv("SERVICE_FINGER")
SERVICE_UPDATE = os.getenv("SERVICE_UPDATE")

TOPIC_GET_STATUS = f"v1/{ROOM_ID}/getStatus"
TOPIC_STATUS_RESPONSE = f"v1/{ROOM_ID}/getStatus/response"

client = mqtt.Client()

def generate_mqtt_password():
    """
    Secret Key ile 10 saniye geçerli bir JWT token üretir.
    Bu token MQTT şifresi olarak kullanılır.
    """
    payload = {"exp": time.time() + 10}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    # PyJWT sürümüne göre bytes dönerse string'e çevir
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def reconnect():
    while True:
        try:
            token = generate_mqtt_password()
            client.username_pw_set(f"{ROOM_ID}", token)
            client.reconnect()  # reconnect
            print(f"[MQTT] Reconnect başarılı, yeni token: {token}")
            break
        except Exception as e:
            print(f"[MQTT] Reconnect başarısız: {e}, 3 sn sonra tekrar denenecek...")
            time.sleep(3)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Bağlandı! (Room ID: {ROOM_ID})")
        # Bağlanınca hemen abone ol
        client.subscribe(f"v1/{ROOM_ID}/getStatus")
        print(f"[MQTT] Abone olundu: {TOPIC_GET_STATUS}")
    else:
        print(f"[MQTT] Bağlantı reddedildi, kod: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnect oldu, rc={rc}")
    if rc != 0:
        print("[MQTT] Tekrar bağlanılıyor...")
        reconnect()

def get_single_service_info(service_name):
    info = {
        "active": "unknown",
        "enabled": "unknown",
        "details": ""
    }

    try:
        res_active = subprocess.run(
            ["systemctl", "is-active", service_name], 
            capture_output=True, text=True
        )
        info["active"] = res_active.stdout.strip()
    except Exception as e:
        info["active"] = f"Error: {str(e)}"

    # 2. Enabled Durumu Sorgusu
    try:
        res_enabled = subprocess.run(
            ["systemctl", "is-enabled", service_name], 
            capture_output=True, text=True
        )
        info["enabled"] = res_enabled.stdout.strip()
    except Exception as e:
        info["enabled"] = f"Error: {str(e)}"

    # 3. Detaylı Log Sorgusu
    try:
        res_status = subprocess.run(
            ["systemctl", "status", service_name, "-n", "20", "--no-pager", "-l"], 
            capture_output=True, text=True
        )
        full_output = res_status.stdout
        if res_status.stderr:
            full_output += "\n[STDERR]\n" + res_status.stderr
        info["details"] = full_output
    except Exception as e:
        info["details"] = f"Log okuma hatası: {str(e)}"
    
    return info

def check_all_services():
    services_map = {
        "lock_service": SERVICE_LOCK,
        "qr_service": SERVICE_QR,
        "fingerprint_service": SERVICE_FINGER,
        "update_listener": SERVICE_UPDATE
    }
    report = {}
    for key, service_name in services_map.items():
        report[key] = get_single_service_info(service_name)
    return report

def on_message(client, userdata, msg):
    # Sadece beklediğimiz topikten gelen mesajları işle
    try:
        if msg.topic == TOPIC_GET_STATUS:
            print("[STATUS] Durum sorgusu isteği alındı...")
            services_report = check_all_services()
            
            try:
                commit_hash = subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"], 
                    cwd=DESTINATION_DIR, text=True
                ).strip()
            except:
                commit_hash = "unknown"

            response = {
                "room_id": ROOM_ID,
                "current_commit": commit_hash,
                "timestamp": time.time(),
                "services": services_report
            }
            client.publish(TOPIC_STATUS_RESPONSE, json.dumps(response))
            print("[STATUS] Rapor gönderildi.")

    except Exception as e:
        print(f"[HATA] Mesaj işleme: {e}")

def run_mqtt_client():
    
    # Callbackleri ata
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    while True:
        try:
            # Her bağlantı denemesinde yeni bir şifre (token) üret
            token = generate_mqtt_password()
            
            # Kullanıcı adı ve şifreyi ayarla
            client.username_pw_set(username=str(ROOM_ID), password=token)
            
            print(f"[SİSTEM] Bağlanılıyor... (IP: {MQTT_IP}, User: {ROOM_ID})")
            client.connect(MQTT_IP, MQTT_PORT, 60)
            
            # Arka planda dinlemeye başla (Blocking yapmaz)
            client.loop_start()
            
            # Programın sürekli çalışmasını sağla
            while True:
                # Bağlantı koparsa loop durmaz ama biz durumu kontrol edebiliriz
                # Burada ana thread'i canlı tutuyoruz.
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[SİSTEM] Çıkış yapılıyor...")
            client.loop_stop()
            client.disconnect()
            sys.exit(0)
            
        except Exception as e:
            print(f"[SİSTEM] Kritik Hata veya Bağlantı Koptu: {e}")
            client.loop_stop()
            print("[SİSTEM] 3 saniye sonra tekrar deneniyor...")
            time.sleep(3)

if __name__ == "__main__":
    run_mqtt_client()