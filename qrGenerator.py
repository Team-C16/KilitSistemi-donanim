import requests
import qrcode
import pygame
from pygame.locals import QUIT
from PIL import Image
import io

# API'den QR kodu verisini al
url = "http://127.0.0.1:8001/getQRCodeToken"
headers = {"Content-Type": "application/json"}
data = '{"room_id": 1}'
response = requests.post(url, headers=headers, data=data, verify=False)

# Eğer API başarılı bir yanıt dönerse
if response.status_code == 200:
    qr_data = response.text  # API'den gelen QR kodu verisi

    # QR kodu üret
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Pygame başlat
    pygame.init()

    # Ekran çözünürlüğünü otomatik olarak al
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h

    # Tam ekran modunda ekran aç
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

    # QR kodunu PIL image'dan Pygame yüzeyine dönüştür
    img = img.convert("RGB")  # RGB formatına dönüştür
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')  # QR kodunu byte formatında kaydet
    img_byte_arr.seek(0)
    qr_surface = pygame.image.load(img_byte_arr)  # Pygame yüzeyine yükle

    # QR kodunu ekranın yüksekliğine göre yeniden boyutlandır
    qr_resized = pygame.transform.scale(qr_surface, (int(screen_height * qr_surface.get_width() / qr_surface.get_height()), screen_height))

    # QR kodunun ekranın ortasına yerleştirilmesi için sol kenar boşluğunu hesapla
    qr_width = qr_resized.get_width()
    left_margin = (screen_width - qr_width) // 2  # Ekranın ortasında olacak şekilde konumlandır

    # Ekranın tamamını kaplayan beyaz bir arka plan
    screen.fill((255, 255, 255))  # Arka planı beyaz yap
    screen.blit(qr_resized, (left_margin, 0))  # QR kodunu ekranın ortasında yerleştir

    # Ekranı güncelle
    pygame.display.flip()

    # Ekranı kapatmak için kullanıcıdan bir çıkış bekle
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

    # Pygame'i sonlandır
    pygame.quit()

else:
    print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
