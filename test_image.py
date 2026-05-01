#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import serial
import time
import subprocess
from PIL import Image
import os

# Komut Kodları
CMD_FINGER_DETECT = 0x21
CMD_GET_IMAGE = 0x20
CMD_UP_IMAGE_CODE = 0x22

def send_command(ser, cmd_code, data_len=0, data_bytes=[]):
    """Modüle komut gönderir"""
    cmd = bytearray(26)
    CKS = 0
    cmd[0:2] = (0xAA55).to_bytes(2, 'little') # 0x55 0xAA
    cmd[2] = 0x00
    cmd[3] = 0x00
    cmd[4:6] = cmd_code.to_bytes(2, 'little')
    cmd[6:8] = data_len.to_bytes(2, 'little')
    
    for i in range(data_len):
        cmd[8+i] = data_bytes[i]
        
    for i in range(24):
        CKS += cmd[i]
        
    cmd[24:26] = CKS.to_bytes(2, 'little')
    ser.write(cmd)

def read_response(ser, expected_len=26, timeout=3):
    """Modülden standart cevap okur"""
    start_time = time.time()
    while ser.inWaiting() < expected_len:
        time.sleep(0.01)
        if time.time() - start_time > timeout:
            return -1, None
    
    rps = ser.read(expected_len)
    if rps[0] == 0xAA and rps[1] == 0x55: # Response Prefix
        ret_code = int.from_bytes(rps[8:10], 'little')
        return ret_code, rps
    return -1, None

def extract_image_data(rx_data):
    """Response Data paketlerinden ham pikselleri ayıklar"""
    pixels = bytearray()
    idx = 0
    while idx < len(rx_data) - 8:
        # Response Data Prefix = 0x5AA5 (Little Endian: 0xA5, 0x5A)
        if rx_data[idx] == 0xA5 and rx_data[idx+1] == 0x5A:
            # Veri uzunluğunu al (LEN_L, LEN_H)
            length = rx_data[idx+6] + (rx_data[idx+7] << 8)
            data_start = idx + 8
            data_end = data_start + length
            
            if data_end <= len(rx_data):
                # İlk 2 byte: Paket Sıra Numarası (SN)
                # Sonraki 2 byte: Paketteki Piksel Sayısı (örn: 0xf0 0x01 = 496)
                # Dolayısıyla gerçek pikseller tam olarak 5. byte'tan (data_start + 4) başlıyor
                if length > 4:
                    pixels.extend(rx_data[data_start+4 : data_end])
            
            idx = data_end + 2 # Checksum atla
        else:
            idx += 1
    return pixels

def change_baudrate(ser, baud_multiplier):
    """Baud rate değiştirir. 8 = 921600 bps, 5 = 115200 bps"""
    send_command(ser, 0x0002, 5, [0x03, baud_multiplier, 0x00, 0x00, 0x00])
    ret, _ = read_response(ser)
    return ret == 0

def init_sensor_connection():
    # Önce 921600 deniyoruz (belki daha önce yükseltilmiştir)
    try:
        ser = serial.Serial('/dev/serial0', 921600, timeout=1)
        send_command(ser, CMD_FINGER_DETECT)
        ret, _ = read_response(ser, timeout=1)
        if ret != -1:
            print("Sensör zaten 921600 baud hızında çalışıyor!")
            return ser
        ser.close()
    except:
        pass

    # Eğer 921600 yanıt vermezse, varsayılan 115200 deneriz
    try:
        ser = serial.Serial('/dev/serial0', 115200, timeout=1)
        send_command(ser, CMD_FINGER_DETECT)
        ret, _ = read_response(ser, timeout=1)
        if ret != -1:
            print("Sensör 115200 baud hızında bulundu. 921600'e yükseltiliyor...")
            if change_baudrate(ser, 8): # 8 = 921600 bps
                print("Hız yükseltme komutu gönderildi!")
                time.sleep(0.5)
                ser.close()
                # Yeni hızda tekrar aç
                ser_fast = serial.Serial('/dev/serial0', 921600, timeout=1)
                return ser_fast
            else:
                print("Hız yükseltilemedi, 115200 ile devam ediliyor.")
                return ser
    except Exception as e:
        print(f"Seri port hatası: {e}")
        return None
    return None

def main():
    print("Seri port aranıyor ve en yüksek hıza ayarlanıyor...")
    ser = init_sensor_connection()
    if not ser:
        print("Sensör ile hiçbir hızda iletişim kurulamadı!")
        return

    ser.reset_input_buffer()
    ser.reset_output_buffer()

    try:
        while True:
            print("\n==============================================")
            print("Sensör hazır. Lütfen parmağınızı okuyucuya yerleştirin...")
            
            # 1. Parmak Bekle
            while True:
                send_command(ser, CMD_FINGER_DETECT)
                ret, response = read_response(ser)
                if ret == 0 and response and response[10] == 1: 
                    break
                time.sleep(0.1)
                
            print("Parmak algılandı! Görüntü alınıyor...")
            
            # 2. Görüntüyü Sensör Ram'ine Al
            time.sleep(0.2) 
            send_command(ser, CMD_GET_IMAGE)
            ret, _ = read_response(ser)
            if ret != 0:
                print(f"Görüntü alma başarısız! Hata Kodu: {hex(ret)}")
                continue
                
            print("Görüntü sensöre alındı. YÜKSEK HIZDA Pi'ye indiriliyor...")
            
            # 3. Görüntüyü Pi'ye İndir
            send_command(ser, CMD_UP_IMAGE_CODE)
            
            rx_data = bytearray()
            start_time = time.time()
            
            while True:
                waiting = ser.inWaiting()
                if waiting > 0:
                    rx_data.extend(ser.read(waiting))
                    start_time = time.time()
                else:
                    time.sleep(0.01)
                    if time.time() - start_time > 0.5: # 921600'de indirme çok hızlı bitecek
                        break
                        
                if len(rx_data) >= 66218:
                    break
            
            transfer_time = time.time() - start_time
            print(f"Toplam {len(rx_data)} byte veri alındı.")
            
            # 4. Pikselleri Ayıkla ve BMP Oluştur
            pixels = extract_image_data(rx_data)
            expected_pixels = 242 * 266
            
            if len(pixels) >= expected_pixels:
                pixels = pixels[:expected_pixels]
                img = Image.frombytes('L', (242, 266), bytes(pixels))
                img_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fingerprint_test.png')
                img.save(img_path)
                print(f"Başarılı! Görüntü kaydedildi: {img_path}")
                print("mpv ile ekrana basılıyor...")
                
                subprocess.run(['mpv', '--force-window=immediate', img_path])
            else:
                print(f"HATA: Yeterli piksel verisi gelmedi. Beklenen: {expected_pixels}, Gelen: {len(pixels)}")

            print("Lütfen sensörden parmağınızı ÇEKİN...")
            # Parmağı çekene kadar bekle! (Aynı parmağı üst üste algılamaması için)
            while True:
                send_command(ser, CMD_FINGER_DETECT)
                ret, response = read_response(ser)
                if ret == 0 and response and response[10] == 0: 
                    break # Parmak çekildi
                time.sleep(0.1)
                
            ser.reset_input_buffer()

    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")
    finally:
        ser.reset_input_buffer()
        ser.close()
        print("Seri port güvenle kapatıldı.")

if __name__ == '__main__':
    main()
