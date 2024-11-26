import requests
import qrcode
import pygame
from io import BytesIO
from PIL import Image

# API'den QR kod token'ını al
url = "https://172.18.0.43/getQRCodeToken"
headers = {"Content-Type": "application/json"}
data = '{"room_id": 1}'
response = requests.post(url, headers=headers, data=data,verify=False)

if response.status_code == 200:
    # Gelen JSON'dan QR token'ı al
    qr_token = response.text  # Burada gelen string'i alıyoruz

    # QR kodunu oluştur
    qr = qrcode.make(qr_token)

    # QR kodunu geçici bir byte array'e dönüştür
    qr_byte_arr = BytesIO()
    qr.save(qr_byte_arr)
    qr_byte_arr.seek(0)

    # Pygame başlatma
    pygame.init()
    screen = pygame.display.set_mode((480, 320))  # Ekran çözünürlüğüne göre ayarlayın
    pygame.display.set_caption("QR Code Display")

    # Ekranı beyaz ile doldur
    screen.fill((255, 255, 255))

    # QR kodunu pygame ekranına yükle
    qr_image = pygame.image.load(qr_byte_arr)

    # QR kodunu ekranın ortasına yerleştir
    qr_rect = qr_image.get_rect(center=(240, 160))  # Ekranın ortasına yerleştir
    screen.blit(qr_image, qr_rect)

    # Ekranda göster
    pygame.display.update()

    # Ekranın açık kalmasını sağlamak için bir döngü
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()
else:
    print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
