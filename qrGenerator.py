import requests
import qrcode
import pygame
from pygame.locals import QUIT
from PIL import Image
import io
import jwt
import time
import socket
month_names = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]

jwtsecret = "JWT_SECRET"#DONT FORGET TO CHANGE SECRET

raspberryNodeip = 'pve.izu.edu.tr/kilitSistemi'

# Function to fetch room name from the API
def fetch_room_name():
    global room_name
    # JWT oluşturma (30 saniye içinde geçersiz olacak şekilde ayarlanır)
    encoded_jwt = jwt.encode(
        {
           "exp": time.time() + 300000
        },
        jwtsecret,
        algorithm="HS256"
    )
    print(encoded_jwt)

    url = f"https://{raspberryNodeip}/getQRCodeToken"
    print(url)
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": 1, "token": "{encoded_jwt}", "room_name": 1}}'
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            # Parse the JSON response and get the room_name
            response_data = response.json()
            print(response_data)
            room_name = response_data.get("room_name")  # Oda adını bir kez al ve sakla
        else:
            print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")


# Function to fetch the QR code token from the API
def fetch_qr_token():
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 300000  # 30 saniye içinde geçersiz olacak
        },
        jwtsecret,
        algorithm="HS256"
    )
    url = f"https://{raspberryNodeip}/getQRCodeToken"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": 1, "token": "{encoded_jwt}"}}'
    try:
        response = requests.post(url, headers=headers, data=data)
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
        (int((screen_width/3) * qr_surface.get_width() / qr_surface.get_height()), screen_width/3)
    )
    return qr_resized


def save_ip():
    print("Save ip called")
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 30000  # 30 saniye içinde geçersiz olacak
        },
        jwtsecret,
        algorithm="HS256"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    print(local_ip)
    url = f"http://{raspberryNodeip}/saveIPForRaspberry"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": 1, "jwtToken": "{encoded_jwt}", "ip": "{local_ip}"}}'
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response
        else:
            print(f"API isteği başarısız oldu. IP Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")
    return None

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(0)
# Set up the display
screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
text = save_ip()
print(text)
fetch_room_name()

# Font tanımlama (EKLENDİ)
font = pygame.font.SysFont("Arial", 20)

# Main loop
running = True
last_update_time = 0
qr_surface = None

clock = pygame.time.Clock()

while running:
    clock.tick(1)
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
        left_margin = (0)
        screen.blit(qr_surface, (left_margin, 0))
        current_time = time.localtime()
        # Extract hour, day, and month
        current_hour = current_time.tm_hour
        current_day = current_time.tm_mday
        current_month = current_time.tm_mon
        current_minute = current_time.tm_min
        current_month_name = month_names[current_month - 1]
        time_text = font.render(f"{current_hour:02}.{current_minute:02}  {current_day:02} {current_month_name}", True, (0,0,0))
        screen.blit(time_text, (10, screen_height -30))

        # Room name ekrana yazdırma
        if room_name:
            room_text = font.render(f"Oda Adı: {room_name}", True, (0, 0, 0))  # Siyah renk
            screen.blit(room_text, (10, screen_height - 170))  # Sol altta gösterir
        pygame.display.flip()

pygame.quit()
