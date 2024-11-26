import requests
import qrcode
import pygame
from pygame.locals import QUIT

# API'den QR kodu verisini al
url = "https://172.18.0.43/getQRCodeToken"
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

    # Ekran boyutlarını al
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

    # QR kodunu Pygame yüzeyine aktar
    qr_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    # Arka plan rengini beyaz yap
    screen.fill((255, 255, 255))

    # QR kodunu ekranda ortalayarak göster
    qr_rect = qr_surface.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(qr_surface, qr_rect)

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
