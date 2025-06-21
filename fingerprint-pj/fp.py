#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import serial
import time
import sqlite3

# =================================================================================
# BÖLÜM 1: Sabitler ve Ayarlar (Dokümandan Doğrulandı)
# =================================================================================

# --- Seri Port Ayarları ---
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200 # Dokümandaki varsayılan değer 

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
CMD_UP_CHAR = 0x42      # YENİ KULLANACAĞIMIZ ANAHTAR KOMUT 
CMD_DOWN_CHAR = 0x43    # YENİ KULLANACAĞIMIZ ANAHTAR KOMUT 
CMD_MATCH = 0x62        # YENİ KULLANACAĞIMIZ ANAHTAR KOMUT 

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
# BÖLÜM 2: Veritabanı İşlemleri (YENİ YAPI)
# Şablon verisi artık bu veritabanında saklanacak.
# =================================================================================

DB_FILE = 'merkezi_veritabani.db'

def veritabani_kur():
    """Veritabanını ve kullanıcılar tablosunu yeni yapıya göre oluşturur."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # YENİ SÜTUN: sablon_verisi (BLOB tipi binary veri saklar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT NOT NULL UNIQUE,
            sablon_verisi BLOB NOT NULL,
            kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def kullanici_ekle(kullanici_adi, sablon_verisi):
    """Yeni kullanıcıyı ve parmak izi şablonunu veritabanına kaydeder."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sablon_verisi) VALUES (?, ?)", (kullanici_adi, sablon_verisi))
        conn.commit()
        print(f"Başarılı: '{kullanici_adi}' kullanıcısı ve parmak izi şablonu veritabanına kaydedildi.")
        return True
    except sqlite3.IntegrityError:
        print(f"HATA: '{kullanici_adi}' adlı kullanıcı zaten mevcut.")
        return False
    finally:
        conn.close()

def tum_kullanicilari_al():
    """Doğrulama için tüm kullanıcıları ve şablonlarını veritabanından çeker."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT kullanici_adi, sablon_verisi FROM kullanicilar")
    rows = cursor.fetchall()
    conn.close()
    return rows

# =================================================================================
# BÖLÜM 3: Düşük Seviyeli Modül İletişimi (Genişletildi)
# =================================================================================

def paket_gonder(cmd_code, data_len, data_bytes):
    """Modüle komut paketini oluşturur ve gönderir."""
    # Bu fonksiyon değişmedi
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
    """Modülden gelen cevabı okur ve doğrular."""
    # Bu fonksiyon değişmedi
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
         return ERR_FAIL, None # Checksum hatası
    ret_code = int.from_bytes(rps[8:10], 'little')
    RPS_DATA_BUFFER = rps[10:beklenen_boyut-2]
    return ret_code, RPS_DATA_BUFFER


def veri_paketi_gonder(cmd_code, data_bytes):
    """(DÜZELTİLDİ) Modüle veri paketi gönderir (CMD_DOWN_CHAR için)."""
    # Veri paketi boyutu = 8 byte header + veri boyutu + 2 byte checksum
    veri_uzunlugu = len(data_bytes)
    paket_boyutu = 8 + veri_uzunlugu + 2
    paket = bytearray(paket_boyutu)
    CKS = 0

    paket[0:2] = Command_Data.to_bytes(2, 'little')  # 0xA55A
    paket[4:6] = cmd_code.to_bytes(2, 'little')
    # LEN alanı, RET (2 byte) + DATA (n byte) boyutunu içerir
    paket[6:8] = (veri_uzunlugu).to_bytes(2, 'little')
    paket[8 : 8 + veri_uzunlugu] = data_bytes

    for i in range(paket_boyutu - 2):
        CKS += paket[i]

    paket[paket_boyutu - 2 : paket_boyutu] = CKS.to_bytes(2, 'little')
    ser.write(paket)


# =================================================================================
# BÖLÜM 4: Yüksek Seviyeli Fonksiyonlar (YENİ YAPI)
# =================================================================================

def goruntu_al():
    """Parmak izi görüntüsünü alır."""
    paket_gonder(CMD_GET_IMAGE, 0, [])
    return cevap_al()[0]
# BU FONKSİYONU BÖLÜM 4'E EKLEYİN

def parmak_algila():
    """Sensörde parmak olup olmadığını kontrol eder."""
    paket_gonder(0x0021, 0, []) # CMD_FINGER_DETECT komutunu gönder
    ret, data = cevap_al()

    if ret == ERR_SUCCESS:
        # Komut başarılıysa, data'nın ilk byte'ı durumu belirtir
        # data[0] == 1 -> Parmak var
        finger_is_present = (data[0] == 1)
        return finger_is_present
    else:
        # Komut başarısız olduysa, parmak yok varsay
        return False

def sablon_olustur(buffer_id):
    """Görüntüden şablon (karakteristik dosya) oluşturur."""
    paket_gonder(CMD_GENERATE, 2, [buffer_id, 0x00])
    return cevap_al()[0]

def sablonlari_birlestir():
    """Üç RamBuffer'daki şablonları birleştirip ana şablonu oluşturur."""
    paket_gonder(CMD_MERGE, 3, [0x00, 0x00, 0x03])
    return cevap_al()[0]

def sablonu_yukle(buffer_id):
    """(YENİ) Şablonu modülden Raspberry Pi'ye yükler."""
    print("Şablon modülden yükleniyor...")
    paket_gonder(CMD_UP_CHAR, 2, [buffer_id, 0x00])
    
    # Modül önce şablon boyutunu içeren bir cevap paketi gönderir
    ret, data = cevap_al()
    if ret != ERR_SUCCESS:
        print("HATA: Şablon yükleme başlatılamadı.")
        return None
    
    # Dokümanda belirtildiği gibi, ardından asıl şablonu içeren bir Veri Paketi gönderir 
    # Örnekte şablon boyutu 498, paket boyutu 498+header+checksum = 508
    sablon_boyutu = int.from_bytes(data[0:2], 'little') # Örn: 498
    paket_boyutu = sablon_boyutu + 12 # Header + RET + Checksum = 12
    
    ret_data, data_data = cevap_al(beklenen_boyut=paket_boyutu)
    if ret_data == ERR_SUCCESS:
        print("Şablon başarıyla yüklendi.")
        return data_data
    else:
        print("HATA: Şablon veri paketini alırken hata oluştu.")
        return None

def sablonu_indir(buffer_id, sablon_verisi):
    """(DÜZELTİLDİ) Şablonu Raspberry Pi'den modüle indirir."""
    # Adım 1: Modülü veri almaya hazırlamak için hazırlık komutu gönder.
    # DATA alanı, gelecek olan Command Data Packet'in DATA kısmının boyutunu içerir.
    # DATA kısmı = 2 byte RamBufferID + 498 byte şablon verisi = 500 byte.
    # PDF'e göre LEN alanı bu veri paketinin boyutunu belirtmeli.
    # Örnekte şablon 498 byte, toplam veri 500 byte.
    gelecek_veri_boyutu = len(sablon_verisi) + 2 # Şablon + BufferID
    paket_gonder(CMD_DOWN_CHAR, 2, gelecek_veri_boyutu.to_bytes(2, 'little'))
    
    # Modülün "veri almaya hazırım" cevabını bekle.
    ret, _ = cevap_al()
    if ret != ERR_SUCCESS:
        print(f"HATA: Modül veri indirmeyi kabul etmedi. Kod: {hex(ret)}")
        return ret
    
    # Adım 2: Modül hazır olduğuna göre, asıl şablonu içeren veri paketini gönder.
    # Veri paketinin DATA kısmı: [2 byte RamBufferID] + [n byte Şablon Verisi]
    veri_paketi_gonder(CMD_DOWN_CHAR, buffer_id.to_bytes(2, 'little') + sablon_verisi)
    
    # Veri paketinden sonra modülün son onayını al.
    # Bu cevap paketi daha kısadır (12 byte) 
    return cevap_al(beklenen_boyut=12)[0]

def sablonlari_eslestir(buffer_id1, buffer_id2):
    """(YENİ) Modülün RAM'indeki iki şablonu eşleştirir."""
    paket_gonder(CMD_MATCH, 4, [buffer_id1, 0, buffer_id2, 0])
    ret, _ = cevap_al()
    return ret == ERR_SUCCESS

# =================================================================================
# BÖLÜM 5: Ana Uygulama Menüsü (YENİ YAPI)
# =================================================================================

# MEVCUT menu_yeni_kayit FONKSİYONUNU SİLİP BUNU YAPIŞTIRIN

# MEVCUT menu_yeni_kayit FONKSİYONUNU SİLİP BUNU YAPIŞTIRIN

def menu_yeni_kayit():
    """(SON SÜRÜM) Yeni kullanıcıyı kaydeder ve kopya kontrolü yapar."""
    print("\n--- YENİ PARMAK İZİ KAYDI (Kopya Kontrollü) ---")
    kullanici_adi = input("Lütfen kullanıcı adını girin: ")

    # 3 adımlı kayıt tarama işlemi (Bu kısımda değişiklik yok)
    for i in range(1, 4):
        print(f"\nAdım {i}/3: Lütfen parmağınızı sensöre yerleştirin...")
        print("(Sensörün boş olması bekleniyor...)")
        while parmak_algila():
            time.sleep(0.1)
        print("Hazır olduğunuzda parmağınızı sensöre koyun.")
        while not parmak_algila():
            time.sleep(0.1)
        print("Parmak algılandı, işleniyor...")

        if goruntu_al() != ERR_SUCCESS:
            print("HATA: Görüntü alınamadı, lütfen tekrar deneyin.")
            return
        if sablon_olustur(i-1) != ERR_SUCCESS:
            print("HATA: Parmak izi kalitesi düşük veya şablon oluşturulamadı.")
            return
        print(f"Adım {i} başarılı. Lütfen parmağınızı kaldırın.")

    print("\n3 tarama tamamlandı. Şablonlar birleştiriliyor...")
    if sablonlari_birlestir() != ERR_SUCCESS:
        print("HATA: Şablonlar birleştirilemedi.")
        return
        
    yeni_sablon = sablonu_yukle(0)
    if not yeni_sablon:
        print("HATA: Şablon modülden alınamadığı için kayıt başarısız.")
        return

    # =================================================================
    # YENİ EKLENEN KOPYA KONTROLÜ BÖLÜMÜ
    # =================================================================
    print("\nOluşturulan parmak izi, mevcut kayıtlarla karşılaştırılıyor...")
    kayitli_kullanicilar = tum_kullanicilari_al()
    kopya_bulundu = False

    if kayitli_kullanicilar:
        # Yeni şablonu modülün RamBuffer0'ına indiriyoruz
        if sablonu_indir(0, yeni_sablon) != ERR_SUCCESS:
            print("HATA: Kopya kontrolü için yeni şablon modüle indirilemedi.")
            return

        for mevcut_kullanici, kayitli_sablon in kayitli_kullanicilar:
            # Mevcut her bir şablonu RamBuffer1'e indirip karşılaştırıyoruz
            if sablonu_indir(1, kayitli_sablon) != ERR_SUCCESS:
                continue # Bu şablonu atla, sonrakiyle devam et

            if sablonlari_eslestir(0, 1):
                print(f"\n!!! UYARI !!!")
                print(f"Bu parmak izi zaten '{mevcut_kullanici}' adına veritabanında kayıtlı.")
                print("Yeni kayıt işlemi iptal edildi.")
                kopya_bulundu = True
                break # Kopya bulununca döngüden çık
    
    # Döngü bittiğinde kopya bulunmadıysa kaydı gerçekleştir
    if not kopya_bulundu:
        print("Parmak izi benzersiz. Kayıt veritabanına ekleniyor...")
        kullanici_ekle(kullanici_adi, yeni_sablon)
    # =================================================================
    # KOPYA KONTROLÜ SONU
    # =================================================================

# MEVCUT menu_kimlik_dogrulama FONKSİYONUNU SİLİP BUNU YAPIŞTIRIN

def menu_kimlik_dogrulama():
    """(DÜZELTİLDİ) Parmak izini, veritabanındaki tüm şablonlarla eşleştirir."""
    print("\n--- KİMLİK DOĞRULAMA (Merkezi Model) ---")
    
    kayitli_kullanicilar = tum_kullanicilari_al()
    if not kayitli_kullanicilar:
        print("Veritabanında hiç kayıtlı kullanıcı bulunamadı!")
        return

    # 1. Anlık parmak izini tara ve RamBuffer0'a bir şablon oluştur
    print("Doğrulama için parmağınızı yerleştirin...")

    # DÜZELTME BAŞLANGICI: Sabit bekleme yerine akıllı bekleme döngüleri
    
    # a. Önce parmağın çekilmiş olduğundan emin olalım (önceki işlemden kalmış olabilir)
    print("(Sensörün boş olması bekleniyor...)")
    while parmak_algila():
        time.sleep(0.1)
    
    # b. Şimdi parmağın konulmasını bekle
    # Parmağınızı sensöre yerleştirene kadar burada sabırla bekler.
    print("Hazır olduğunuzda parmağınızı sensöre koyun.")
    while not parmak_algila():
        time.sleep(0.1)
        
    # DÜZELTME SONU

    print("Parmak algılandı, veritabanı taranıyor...")
    if goruntu_al() != ERR_SUCCESS or sablon_olustur(0) != ERR_SUCCESS:
        print("HATA: Parmak izi okunamadı.")
        return

    # 2. Veritabanındaki her şablon için döngü başlat
    eslesme_bulundu = False
    for kullanici, kayitli_sablon in kayitli_kullanicilar:
        print(f"-> '{kullanici}' kullanıcısının şablonuyla karşılaştırılıyor...")
        
        # 3. Kayıtlı şablonu Pi'den modülün RamBuffer1'ine indir
        if sablonu_indir(1, kayitli_sablon) != ERR_SUCCESS:
            print(f"UYARI: '{kullanici}' şablonu modüle indirilemedi.")
            continue
            
        # 4. RamBuffer0 (anlık) ve RamBuffer1'i (kayıtlı) eşleştir
        if sablonlari_eslestir(0, 1):
            print("\n-----------------------------")
            print(f"   KİMLİK DOĞRULANDI!")
            print(f"   Hoş Geldiniz, {kullanici}")
            print("-----------------------------")
            eslesme_bulundu = True
            break # Eşleşme bulununca döngüden çık
    
    if not eslesme_bulundu:
        print("\n-----------------------------")
        print("   KİMLİK DOĞRULANAMADI!")
        print("   Eşleşen parmak izi bulunamadı.")
        print("-----------------------------")


def main():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print("Seri port başarıyla açıldı.")
        time.sleep(0.5) # Modülün başlaması için kısa bir bekleme
    except serial.SerialException as e:
        print(f"HATA: Seri port açılamadı: {e}")
        return

    veritabani_kur()
    print("Merkezi veritabanı kontrol edildi/oluşturuldu.")
    time.sleep(1)

    while True:
        print("\n========== AKILLI KİLİT SİSTEMİ (MERKEZİ MODEL) ==========")
        print("1. Yeni Parmak İzi Kaydet")
        print("2. Kimlik Doğrula")
        print("3. Çıkış")
        secim = input("Seçiminiz [1-3]: ")
        if secim == '1':
            menu_yeni_kayit()
        elif secim == '2':
            menu_kimlik_dogrulama()
        elif secim == '3':
            break
        else:
            print("Geçersiz seçim!")
        input("\nDevam etmek için Enter'a basın...")

    if ser and ser.is_open:
        ser.close()
    print("Program sonlandırıldı.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        if ser and ser.is_open:
            ser.close()
        print("\nProgram kullanıcı tarafından sonlandırıldı.")