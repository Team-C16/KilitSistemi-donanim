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




# Dinlenecek Topic
TOPIC_UPDATE = f"v1/{ROOM_ID}/update"

# --- Yardımcı Fonksiyonlar ---

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

# --- MQTT Callback Fonksiyonları ---

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Bağlandı! (Room ID: {ROOM_ID})")
        # Bağlanınca hemen abone ol
        client.subscribe(TOPIC_UPDATE)
        print(f"[MQTT] Abone olundu: {TOPIC_UPDATE}")
    else:
        print(f"[MQTT] Bağlantı reddedildi, kod: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Bağlantı koptu (rc={rc})")
    if rc != 0:
        print("[MQTT] Beklenmedik kopuş, tekrar bağlanılacak...")
        # Paho-MQTT loop_start kullanıldığında otomatik reconnect dener,
        # ancak token süresi dolduysa manuel müdahale gerekebilir.
        # Aşağıdaki reconnect fonksiyonu bunu halledecek.

def apply_update(commit_id):
    print(f"🚀 [SİSTEM] Versiyon değişimi başlatılıyor. Hedef: {commit_id}")
    try:
        print("[GIT] Sunucu ile senkronize olunuyor (Fetch)...")
        subprocess.run(
            ["git", "fetch", "origin", BRANCH_NAME],
            cwd=DESTINATION_DIR,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"[GIT] Dosyalar {commit_id} sürümüne getiriliyor...")
        subprocess.run(
            ["git", "reset", "--hard", commit_id],
            cwd=DESTINATION_DIR,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Dosyalar başarıyla güncellendi.")

        print(f"[SYSTEM] {SERVICE_QR} servisi yeniden başlatılıyor...")
        subprocess.run(["sudo", "systemctl", "restart", SERVICE_QR], check=True)
        print(f"[SYSTEM] {SERVICE_LOCK} yeniden başlatılıyor...")
        subprocess.run(["sudo", "systemctl", "restart", SERVICE_LOCK], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ [GIT HATASI] İşlem başarısız: {e}")
        if e.stderr:
            print(f"Detay: {e.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"❌ [GENEL HATA] {e}")



def on_message(client, userdata, msg):
    # Sadece beklediğimiz topikten gelen mesajları işle
    if msg.topic == TOPIC_UPDATE:
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            
            # commitID'yi çek
            commit_id = data.get("commitID")
            
            if commit_id:
                apply_update(commit_id)
            else:
                print("[UYARI] Mesajda 'commitID' bulunamadı.")

        except json.JSONDecodeError:
            print("[HATA] Gelen mesaj JSON formatında değil.")
        except Exception as e:
            print(f"[HATA] Mesaj işlenirken hata oluştu: {e}")

# --- Ana Bağlantı Döngüsü ---

def run_mqtt_client():
    client = mqtt.Client()
    
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