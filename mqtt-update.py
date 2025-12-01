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
TOPIC_GET_STATUS = f"v1/{ROOM_ID}/getStatus"
TOPIC_STATUS_RESPONSE = f"v1/{ROOM_ID}/getStatus/response"

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
        client.subscribe([(TOPIC_UPDATE, 0), (TOPIC_GET_STATUS, 0)])
        print(f"[MQTT] Abone olundu: {TOPIC_UPDATE}")
        print(f"[MQTT] Abone olundu: {TOPIC_GET_STATUS}")
    else:
        print(f"[MQTT] Bağlantı reddedildi, kod: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Bağlantı koptu (rc={rc})")
    if rc != 0:
        print("[MQTT] Beklenmedik kopuş, tekrar bağlanılacak...")
        # Paho-MQTT loop_start kullanıldığında otomatik reconnect dener,
        # ancak token süresi dolduysa manuel müdahale gerekebilir.
        # Aşağıdaki reconnect fonksiyonu bunu halledecek.

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

        elif msg.topic == TOPIC_GET_STATUS:
            print("[STATUS] Durum sorgusu alındı...")
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