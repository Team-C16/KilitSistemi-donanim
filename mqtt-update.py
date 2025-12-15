import os
import time
import json
import sys
import subprocess
import jwt
import paho.mqtt.client as mqtt
# from dotenv import load_dotenv

# .env dosyasını yükle
# load_dotenv()

# Değişkenleri al
MQTT_IP = os.getenv("mqttbrokerip")
MQTT_PORT = int(os.getenv("mqttbrokerport", 1883))
ROOM_ID = os.getenv("room_id")
SECRET_KEY = os.getenv("SECRET_KEY")
DESTINATION_DIR = os.getenv("DESTINATION_DIR")
BRANCH_NAME = os.getenv("BRANCH_NAME")
SERVICE_QR = os.getenv("SERVICE_QR")
SERVICE_LOCK = os.getenv("SERVICE_LOCK")
SERVICE_FINGER = os.getenv("SERVICE_FINGER")
SERVICE_UPDATE = os.getenv("SERVICE_UPDATE")





# Dinlenecek Topic
TOPIC_UPDATE = f"v1/{ROOM_ID}/update"

# Client oluşturma
client = mqtt.Client()

# --- Yardımcı Fonksiyonlar ---


def generate_mqtt_password():
    payload = {"exp": time.time() + 30}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    # PyJWT sürümüne göre bytes dönerse string'e çevir
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# --- MQTT Callback Fonksiyonları ---

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
        client.subscribe(f"v1/{ROOM_ID}/update")
        print(f"[MQTT] Abone olundu: {TOPIC_UPDATE}")
    else:
        print(f"[MQTT] Bağlantı reddedildi, kod: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnect oldu, rc={rc}")
    if rc != 0:
        print("[MQTT] Tekrar bağlanılıyor...")
        reconnect()

def apply_update(commit_id):
    print(f"🚀 [SİSTEM] Versiyon değişimi başlatılıyor. Hedef: {commit_id}")

    # --- Git Güncelleme İşlemleri ---
    try:
        print("[GIT] Sunucu ile senkronize olunuyor (Fetch)...")
        subprocess.run(
            ["sudo", "git", "fetch", "origin", BRANCH_NAME],
            cwd=DESTINATION_DIR,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        print(f"[GIT] Dosyalar {commit_id} sürümüne getiriliyor...")
        subprocess.run(
            ["sudo", "git", "reset", "--hard", commit_id],
            cwd=DESTINATION_DIR,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Dosyalar başarıyla güncellendi.")

    except subprocess.CalledProcessError as e:
        print(f"❌ [KRİTİK GIT HATASI] Güncelleme çekilemedi: {e}")
        if e.stderr:
            print(f"Detay: {e.stderr.decode('utf-8')}")
        return  # Dosyalar güncellenemediği için işlem iptal edilir.

    except Exception as e:
        print(f"❌ [GENEL GIT HATASI] Beklenmedik durum: {e}")
        return

    # --- Kütüphane (PIP) Kontrolü ---
    req_file = os.path.join(DESTINATION_DIR, "requirements.txt")
    
    if os.path.exists(req_file):
        try:
            print("[PIP] Yeni kütüphaneler kontrol ediliyor ve yükleniyor...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file, "--break-system-packages"],
                cwd=DESTINATION_DIR,
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print("✅ Kütüphane kurulumu tamamlandı.")

        except subprocess.CalledProcessError as e:
            print(f"❌ [PIP HATASI] Kütüphaneler yüklenirken hata oluştu: {e}")
            if e.stderr:
                print(f"Detay: {e.stderr.decode('utf-8')}")
            # Pip hatası olsa bile servisleri başlatmayı denemeye devam ediyoruz.
    else:
        print("[PIP] requirements.txt bulunamadı, bu adım atlanıyor.")

    # --- QR Servisini Yeniden Başlatma ---
    try:
        print(f"[SYSTEM] {SERVICE_QR} servisi yeniden başlatılıyor...")
        subprocess.run(
            ["sudo", "systemctl", "restart", SERVICE_QR], 
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"✅ {SERVICE_QR} başarıyla yeniden başlatıldı.")

    except subprocess.CalledProcessError as e:
        print(f"❌ [SERVİS HATASI] {SERVICE_QR} başlatılamadı: {e}")
        if e.stderr:
             print(f"Detay: {e.stderr.decode('utf-8')}")

    # --- Kilit Servisini (Kendini) Yeniden Başlatma ---
    try:
        print(f"[SYSTEM] {SERVICE_LOCK} (KENDİM) yeniden başlatılıyor...")
        subprocess.run(
            ["sudo", "systemctl", "restart", SERVICE_LOCK], 
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
    except subprocess.CalledProcessError as e:
        print(f"❌ [SERVİS HATASI] Kendimi ({SERVICE_LOCK}) yeniden başlatamadım: {e}")
        if e.stderr:
             print(f"Detay: {e.stderr.decode('utf-8')}")

def on_message(client, userdata, msg):
    # Sadece beklediğimiz topikten gelen mesajları işle
    try:
        if msg.topic == TOPIC_UPDATE:
            payload = json.loads(msg.payload.decode("utf-8"))
            commit_id = payload.get("commitID")
            if commit_id:
                apply_update(commit_id)
            else:
                print("CommitID bulunamadı.")
    except Exception as e:
        print(f"[HATA] Mesaj işleme: {e}")

# --- Ana Bağlantı Döngüsü ---

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