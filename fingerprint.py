import requests
import base64
import threading
import subprocess
import serial
import time
from gpiozero import LED
import jwt
from flask import Flask, request, jsonify

# Tkinter importları
import tkinter as tk
from tkinter import font as tkfont

led = LED(12)

# =================================================================================
# BÖLÜM 1: Sabitler ve Ayarlar
# =================================================================================

SECRET_KEY = "JWT_SECRET"

room_id = 2

API_BASE = "https://pve.izu.edu.tr/kilitSistemi"

kayitMenu = None

# --- Seri Port Ayarları ---
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200

# --- Paket Tanımlayıcıları ---
Command = 0xAA55
Response = 0x55AA
Command_Data = 0xA55A
Response_Data = 0x5AA5

# --- Komut ve Cevap Kodları ---
CMD_TEST_CONNECTION = 0x01
CMD_GET_IMAGE = 0x20
CMD_GENERATE = 0x60
CMD_MERGE = 0x61
CMD_UP_CHAR = 0x42
CMD_DOWN_CHAR = 0x43
CMD_MATCH = 0x62

# --- Sonuç (Hata) Kodları ---
ERR_SUCCESS = 0x00
ERR_FAIL = 0x01
ERR_VERIFY = 0x10
ERR_BAD_QUALITY = 0x19
ERR_INVALID_BUFFER_ID = 0x26

# --- Global Değişkenler ---
ser = None
RPS_DATA_BUFFER = [0] * 14

# =================================================================================
# BÖLÜM 2: Tkinter Bildirim Fonksiyonları (YENİ BÖLÜM)
# =================================================================================

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

# =================================================================================
# BÖLÜM 4: Yüksek Seviyeli Fonksiyonlar
# =================================================================================

def paket_gonder(cmd_code, data_len, data_bytes):
    cmd = bytearray(26)
    CKS = 0
    cmd[0:2] = Command.to_bytes(2, 'little')
    cmd[4:6] = cmd_code.to_bytes(2, 'little')
    cmd[6:8] = data_len.to_bytes(2, 'little')
    for i in range(data_len):
        cmd[8+i] = data_bytes[i]
    for i in range(24):
        CKS += cmd[i]
    cmd[24:26] = CKS.to_bytes(2, 'little')
    ser.write(cmd)

def cevap_al(beklenen_boyut=26):
    global RPS_DATA_BUFFER
    timeout = time.time() + 3
    while ser.inWaiting() < beklenen_boyut:
        time.sleep(0.01)
        if time.time() > timeout:
            return ERR_FAIL, None
    rps = ser.read(beklenen_boyut)
    CKS = 0
    for i in range(beklenen_boyut - 2):
        CKS += rps[i]
    if CKS.to_bytes(2, 'little') != rps[beklenen_boyut-2:beklenen_boyut]:
        return ERR_FAIL, None
    ret_code = int.from_bytes(rps[8:10], 'little')
    RPS_DATA_BUFFER = rps[10:beklenen_boyut-2]
    return ret_code, RPS_DATA_BUFFER

def veri_paketi_gonder(cmd_code, data_bytes):
    veri_uzunlugu = len(data_bytes)
    paket_boyutu = 8 + veri_uzunlugu + 2
    paket = bytearray(paket_boyutu)
    CKS = 0
    paket[0:2] = Command_Data.to_bytes(2, 'little')
    paket[4:6] = cmd_code.to_bytes(2, 'little')
    paket[6:8] = (veri_uzunlugu).to_bytes(2, 'little')
    paket[8 : 8 + veri_uzunlugu] = data_bytes
    for i in range(paket_boyutu - 2):
        CKS += paket[i]
    paket[paket_boyutu - 2 : paket_boyutu] = CKS.to_bytes(2, 'little')
    ser.write(paket)

def goruntu_al():
    paket_gonder(CMD_GET_IMAGE, 0, [])
    return cevap_al()[0]

def parmak_algila():
    paket_gonder(0x0021, 0, [])
    ret, data = cevap_al()
    if ret == ERR_SUCCESS:
        finger_is_present = (data[0] == 1)
        return finger_is_present
    else:
        return False

def sablon_olustur(buffer_id):
    paket_gonder(CMD_GENERATE, 2, [buffer_id, 0x00])
    return cevap_al()[0]

def sablonlari_birlestir():
    paket_gonder(CMD_MERGE, 3, [0x00, 0x00, 0x03])
    return cevap_al()[0]

def sablonu_yukle(buffer_id):
    print("Şablon modülden yükleniyor...")
    paket_gonder(CMD_UP_CHAR, 2, [buffer_id, 0x00])
    ret, data = cevap_al()
    if ret != ERR_SUCCESS:
        print("HATA: Şablon yükleme başlatılamadı.")
        return None
    sablon_boyutu = int.from_bytes(data[0:2], 'little')
    paket_boyutu = sablon_boyutu + 12
    ret_data, data_data = cevap_al(beklenen_boyut=paket_boyutu)
    if ret_data == ERR_SUCCESS:
        print("Şablon başarıyla yüklendi.")
        return data_data
    else:
        print("HATA: Şablon veri paketini alırken hata oluştu.")
        return None

def sablonu_indir(buffer_id, sablon_verisi):
    gelecek_veri_boyutu = len(sablon_verisi) + 2
    paket_gonder(CMD_DOWN_CHAR, 2, gelecek_veri_boyutu.to_bytes(2, 'little'))
    ret, _ = cevap_al()
    if ret != ERR_SUCCESS:
        print(f"HATA: Modül veri indirmeyi kabul etmedi. Kod: {hex(ret)}")
        return ret
    veri_paketi_gonder(CMD_DOWN_CHAR, buffer_id.to_bytes(2, 'little') + sablon_verisi)
    return cevap_al(beklenen_boyut=12)[0]

def sablonlari_eslestir(buffer_id1, buffer_id2):
    paket_gonder(CMD_MATCH, 4, [buffer_id1, 0, buffer_id2, 0])
    ret, _ = cevap_al()
    return ret == ERR_SUCCESS

def api_tum_kullanicilari_al():
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 30
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": {room_id}, "jwtToken": "{encoded_jwt}"}}'
    r = requests.get(f"{API_BASE}/getAllFingerprints",headers= headers, data=data)
    if r.status_code == 200:
        return r.json()
    else:
        print("API hatası:", r.status_code, r.text)
        return []

def menu_kimlik_dogrulama(stop_event=None):
    print("\n--- KİMLİK DOĞRULAMA BAŞLADI ---")
    while not stop_event.is_set():
        try:
            print("\nDoğrulama için parmağınızı yerleştirin...")
            while parmak_algila():
                show_notification("Lütfen\nParmağınızı\nKaldırın", duration=0)
                if stop_event.is_set():
                    hide_notification()
                    return
                time.sleep(0.5)
            
            hide_notification()

            
            while not parmak_algila():
                if stop_event.is_set():
                    hide_notification()
                    return
                time.sleep(0.5)
            
            hide_notification()
            
            show_notification("Kontrol Ediliyor", duration=2)
            kayitli_kullanicilar = api_tum_kullanicilari_al()
            if goruntu_al() != ERR_SUCCESS or sablon_olustur(0) != ERR_SUCCESS:
                print("HATA: Parmak izi okunamadı.")
                show_notification("Parmak\nOkunamadı", duration=3, color='red')
                time.sleep(1)
                continue

            eslesme_bulundu = False
            for user in kayitli_kullanicilar:
                sablon_b64 = user.get("fingerprint")
                if not sablon_b64:
                    continue
                sablon_bytes = base64.b64decode(sablon_b64)
                if sablonu_indir(1, sablon_bytes) != ERR_SUCCESS:
                    continue
                if sablonlari_eslestir(0, 1):
                    print(f"\n✅ KİMLİK DOĞRULANDI")
                    eslesme_bulundu = True
                    led.on()
                    show_notification("Kilit Açık!", duration=10, color='green')
                    time.sleep(10)
                    led.off()
                    break

            if not eslesme_bulundu:
                show_notification("Eşleşme\nBulunamadı", duration=2, color='red')
                time.sleep(2)
                print("❌ Kimlik doğrulanamadı!")

            time.sleep(1)
        except KeyboardInterrupt:
            hide_notification()
            break

def api_kullanici_ekle(userID, sablon_verisi):
    data = {
        "userID": userID,
        "fingerprint": base64.b64encode(sablon_verisi).decode("utf-8")
    }
    r = requests.post(f"{API_BASE}/registertemplate", json=data)
    return r.json()

def menu_yeni_kayit(userID):
    toplam_adim = 3
    for i in range(1, toplam_adim + 1):
        message = f"Adım {i}/{toplam_adim}\nParmağınızı Koyun"
        show_notification(message, duration=0)
        print(f"{i}. okutma için parmağınızı yerleştirin...")

        while parmak_algila():
            time.sleep(0.1)
        while not parmak_algila():
            time.sleep(0.1)
        
        hide_notification()

        if goruntu_al() != ERR_SUCCESS:
            show_notification("Görüntü alınamadı", duration=2, color='red')
            return {"error": "Görüntü alınamadı"}
        if sablon_olustur(i - 1) != ERR_SUCCESS:
            show_notification("Şablon oluşturulamadı", duration=2, color='red')
            return {"error": "Şablon oluşturulamadı"}

        print(f"{i}. okutma tamamlandı.")
        
        show_notification("Okuma Tamamlandı!\nParmağınızı Çekin", duration=2, color='green')
        time.sleep(1)

    if sablonlari_birlestir() != ERR_SUCCESS:
        show_notification("Şablonlar birleştirilemedi", duration=2, color='red')
        return {"error": "Şablonlar birleştirilemedi"}

    sablon = sablonu_yukle(0)
    if not sablon:
        show_notification("Şablon alınamadı", duration=2, color='red')
        return {"error": "Şablon alınamadı"}

    show_notification("Kayıt Tamamlandı!", duration=10, color='green')
    time.sleep(3)
    result = api_kullanici_ekle(userID, sablon)
    return {"success": True, "api_response": result}

# -------------------------
# Flask Web Server
# -------------------------
app = Flask(__name__)

stop_kimlik_thread = threading.Event()
kimlik_thread = None

@app.route("/yeni_kayit", methods=["POST"])
def yeni_kayit():
    global kimlik_thread, stop_kimlik_thread

    data = request.get_json()
    if not data or "userID" not in data:
        return jsonify({"error": "userID girilmeli"}), 400

    userID = data["userID"]

    if kimlik_thread and kimlik_thread.is_alive():
        stop_kimlik_thread.set()
        kimlik_thread.join(timeout=5)
        if kimlik_thread.is_alive():
            print("Uyarı: Kimlik doğrulama thread'i zamanında durdurulamadı.")

    kayit_result = menu_yeni_kayit(userID)

    stop_kimlik_thread.clear()
    kimlik_thread = threading.Thread(target=menu_kimlik_dogrulama, args=(stop_kimlik_thread,))
    kimlik_thread.start()

    return jsonify(kayit_result)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False))
    flask_thread.start()
    
    tkinter_thread = threading.Thread(target=create_tkinter_app)
    tkinter_thread.start()
    
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    kimlik_thread = threading.Thread(target=menu_kimlik_dogrulama, args=(stop_kimlik_thread,))
    kimlik_thread.start()
    
    flask_thread.join()
    tkinter_thread.join()
    kimlik_thread.join()