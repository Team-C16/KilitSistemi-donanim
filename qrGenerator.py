import requests
import qrcode
import pygame
from pygame.locals import QUIT
from PIL import Image
import io

# Function to fetch the QR code token from the API
def fetch_qr_token():
    url = "http://127.0.0.1:8001/getQRCodeToken"
    headers = {"Content-Type": "application/json"}
    data = '{"room_id": 1}'
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code == 200:
            # Parse the JSON response and get the token
            response_data = response.json()
            return response_data.get("token")  # Get the 'token' field from the response
        else:
            print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")
    return None

# Function to generate a QR code surface
def generate_qr_code_surface(qr_data, screen_height):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    img = img.convert("RGB")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    qr_surface = pygame.image.load(img_byte_arr)

    qr_resized = pygame.transform.scale(
        qr_surface,
        (int(screen_height * qr_surface.get_width() / qr_surface.get_height()), screen_height)
    )
    return qr_resized

# Initialize Pygame
pygame.init()

# Set up the display
screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

# Main loop
running = True
last_update_time = 0
qr_surface = None

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

   
    current_time = pygame.time.get_ticks()
    if current_time - last_update_time > 57000 or qr_surface is None:  # 57000 ms = 57 seconds beacuse we dont want to show expired token in screen so its 57
        last_update_time = current_time
        qr_token = fetch_qr_token()
        if qr_token:
            qr_surface = generate_qr_code_surface(qr_token, screen_height)

    # Update the display
    if qr_surface:
        screen.fill((255, 255, 255))  # Clear the screen with white background
        qr_width = qr_surface.get_width()
        left_margin = (screen_width - qr_width) // 2
        screen.blit(qr_surface, (left_margin, 0))
        pygame.display.flip()

pygame.quit()
