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
                pixels.extend(rx_data[data_start:data_end])
            
            idx = data_end + 2 # Checksum atla
        else:
            idx += 1
    return pixels

def main():
    print("Seri port açılıyor... (/dev/ttyS0, 115200)")
    try:
        # Timeout eklenmesi cihazın donmasını engeller
        ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        ser.reset_input_buffer() # İçeride kalan eski bozuk verileri temizle
        ser.reset_output_buffer()
    except Exception as e:
        print(f"Seri port açılamadı! Lütfen USB-TTL dönüştürücü veya pin bağlantısını kontrol et. Hata: {e}")
        return

    try:
        print("\nSensör hazır. Lütfen parmağınızı okuyucuya yerleştirin...")
        
        # 1. Parmak Bekle
        while True:
            send_command(ser, CMD_FINGER_DETECT)
            ret, _ = read_response(ser)
            if ret == 0: # Parmak algılandı
                break
            time.sleep(0.1)
            
        print("Parmak algılandı! Görüntü alınıyor...")
        
        # 2. Görüntüyü Sensör Ram'ine Al
        send_command(ser, CMD_GET_IMAGE)
        ret, _ = read_response(ser)
        if ret != 0:
            print("Görüntü alma başarısız!")
            return
            
        print("Görüntü sensöre alındı. Pi'ye indiriliyor (Bu işlem birkaç saniye sürebilir)...")
        
        # 3. Görüntüyü Pi'ye İndir
        send_command(ser, CMD_UP_IMAGE_CODE)
        
        # Data paketleri gelmeye başlayacak. Toplam veri ~66218 byte.
        rx_data = bytearray()
        start_time = time.time()
        
        # Veri akışı bitene kadar veya 6 saniye geçene kadar oku
        while True:
            waiting = ser.inWaiting()
            if waiting > 0:
                rx_data.extend(ser.read(waiting))
                start_time = time.time() # Zaman aşımını sıfırla
            else:
                time.sleep(0.01)
                # 1 saniye boyunca hiç veri gelmezse indirme bitmiştir
                if time.time() - start_time > 1.0:
                    break
                    
            if len(rx_data) >= 66218:
                break
                
        print(f"Toplam {len(rx_data)} byte veri alındı. Görüntü işleniyor...")
        
        # 4. Pikselleri Ayıkla ve BMP Oluştur
        pixels = extract_image_data(rx_data)
        
        # Beklenen çözünürlük: 242 x 266 = 64372 pixel
        expected_pixels = 242 * 266
        
        if len(pixels) >= expected_pixels:
            pixels = pixels[:expected_pixels]
            
            # Pikselleri Image objesine çevir
            img = Image.frombytes('L', (242, 266), bytes(pixels))
            img_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fingerprint_test.png')
            img.save(img_path)
            print(f"\nBaşarılı! Görüntü kaydedildi: {img_path}")
            print("mpv ile ekrana basılıyor...")
            
            # 5. MPV ile göster
            subprocess.Popen(['mpv', '--force-window=immediate', img_path])
        else:
            print(f"HATA: Yeterli piksel verisi gelmedi. Beklenen: {expected_pixels}, Gelen: {len(pixels)}")
            print("Lütfen bağlantıları kontrol edin ve tekrar deneyin.")

    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")
    finally:
        ser.reset_input_buffer()
        ser.close()
        print("Seri port güvenle kapatıldı.")

if __name__ == '__main__':
    main()
