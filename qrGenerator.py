import requests
import qrcode
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
from PIL import Image
import io
import jwt
import time
import socket
from datetime import datetime, timedelta, UTC
from pygame.locals import *

# JWT secret key
jwtsecret = "JWT_SECRET"

# Raspberry Node IP
raspberryNodeip = '172.18.6.111:32002'

scroll_indices = {}
last_scroll_time = 0


# Renk Paleti (Modern, Flat UI)
COLORS = {
    "background": (245, 248, 255),      # Slightly blue-tinted background
    "primary": (41, 98, 255),           # Richer blue for primary elements
    "secondary": (72, 101, 129),        # Deep blue-gray
    "success": (46, 204, 113),          # Vibrant green
    "danger": (231, 76, 60),            # Softer red
    "warning": (241, 196, 15),          # Golden yellow
    "info": (52, 152, 219),             # Bright blue
    "light": (255, 255, 255),           # Pure white
    "dark": (44, 62, 80),               # Deep blue-gray
    "white": (255, 255, 255),           # White
    "text_primary": (44, 62, 80),       # Dark blue-gray text
    "text_secondary": (127, 140, 141),  # Medium gray text
    "available": (46, 204, 113),        # Vibrant green for available
    "unavailable": (231, 76, 60),       # Softer red for unavailable
    "border": (214, 219, 233),          # Subtle border color
    "highlight": (241, 196, 15),        # Highlight color
}

def transform_schedule(api_data):
    # Helper function to get the day of the week
    def get_day_of_week(date_str):
        # Convert string to datetime object
        date_obj = datetime.fromisoformat(date_str[:-1])  # Remove 'Z' from ISO string
        # Get the day of the week (0=Monday, 6=Sunday)
        date_obj = date_obj + timedelta(days=1)
        days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        return days_of_week[date_obj.weekday()]

    # Initialize the schedule dictionary
    transformed_data = {day: {f"{hour:02d}:00": {"durum": "Boş", "aktivite": "", "düzenleyen": ""} for hour in range(9, 19)} for day in 
                     ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma","Cumartesi","Pazar"]}
    # Populate the ders_programi dictionary based on API data
    for entry in api_data['schedule']:
        day_of_week = get_day_of_week(entry['day'])
        hour = entry['hour'][:5]  # Extract just the hour:minute part (e.g., "10:00")
        cell = transformed_data[day_of_week][hour]
        if cell["durum"] == "Boş":
            cell["durum"] = "Dolu"
            cell["entries"] = [{"aktivite": entry['title'], "düzenleyen": entry['username']}]
        else:
            cell["entries"].append({"aktivite": entry['title'], "düzenleyen": entry['username']})


    return transformed_data

# Gradient arka plan çizme fonksiyonu
def draw_gradient_background(screen, color1, color2):
    for y in range(screen_height):
        # Smoother gradient calculation
        factor = y / screen_height
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen_width, y))

# QR kod oluşturma fonksiyonu
def generate_qr_code_surface(qr_data, screen_width, screen_height):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert("RGBA")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    qr_surface = pygame.image.load(img_byte_arr)
    
    qr_size = int(screen_width // 4)
    qr_resized = pygame.transform.scale(qr_surface, (qr_size, qr_size))
    
    # Create a slightly larger surface for frame and shadow
    final_size = qr_size + 8  # Add padding for frame
    final_surface = pygame.Surface((final_size, final_size), pygame.SRCALPHA)
    
    
    # Draw white frame
    pygame.draw.rect(final_surface, COLORS["light"], (5, 5, qr_size + 10, qr_size + 10), 0, 10)
    
    # Place QR code on frame
    final_surface.blit(qr_resized, (10, 10))
    
    return final_surface

def fetch_room_name():
    global room_name
    # JWT oluşturma (300000 saniye içinde geçersiz olacak şekilde ayarlanır)
    encoded_jwt = jwt.encode(
        {
           "exp": time.time() + 300000
        },
        jwtsecret,
        algorithm="HS256"
    )
    print(encoded_jwt)
    url = f"http://{raspberryNodeip}/getQRCodeToken"
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
            return room_name
        else:
            print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")
    return None


# Ders programı tablosu çizme fonksiyonu
def draw_schedule_table(screen, fonts):
    today = datetime.now().strftime("%A")
    dict = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı",
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }
    today_tr = dict.get(today,'Pazartesi')
    margin = screen_width // 100
    header_height = 60
    row_height = screen_height // 12
    time_column_width = screen_width // 20
    column_width = screen_width // 8
    border_radius = 10  # Rounded corners

    date_obj = datetime.now()

    days_in_english = [date_obj.strftime('%A'), (date_obj+ timedelta(days = 1)).strftime("%A"), (date_obj+ timedelta(days = 2)).strftime("%A"), (date_obj+ timedelta(days = 3)).strftime("%A"),(date_obj+ timedelta(days = 4)).strftime("%A")]
    days = [dict.get(day, "Pazartesi") for day in days_in_english]

    hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

    table_width = time_column_width + len(days) * column_width
    table_x = screen_width * 0.31
    table_y = 30

    # Draw table background with rounded corners
    table_bg_rect = pygame.Rect(table_x - 10, table_y - 10, 
                              table_width + 20, header_height + len(hours) * row_height + 20)
    # Add subtle shadow
    shadow_surface = pygame.Surface((table_bg_rect.width, table_bg_rect.height), pygame.SRCALPHA)
    shadow_surface.fill((0, 0, 0, 20))
    screen.blit(shadow_surface, (table_bg_rect.x + 5, table_bg_rect.y + 5))

    pygame.draw.rect(screen, COLORS["light"], table_bg_rect, 0, border_radius)
    

    # Header row with gradient
    header_rect = pygame.Rect(table_x, table_y, table_width, header_height)
    draw_gradient_rect(screen, COLORS["primary"], darken_color(COLORS["primary"]), header_rect, border_radius)
    
    # Time column header (top-left cell)
    time_header_rect = pygame.Rect(table_x, table_y, time_column_width, header_height)
    pygame.draw.rect(screen, COLORS["secondary"], time_header_rect, 0)
    draw_text(screen, "Saat", fonts["day"], COLORS["white"], time_header_rect, "center", "center")

    # Day headers
    for i, day in enumerate(days):
        day_rect = pygame.Rect(table_x + time_column_width + i * column_width, table_y, column_width, header_height)
        
        # Highlight current day
        if day == today_tr:
            pygame.draw.rect(screen, COLORS["info"], day_rect, 0)
            draw_text(screen, day, fonts["day"], COLORS["white"], day_rect, "center", "center")
            # Add "Bugün" indicator
            today_indicator = fonts["title_small"].render("Bugün", True, COLORS["light"])
            indicator_rect = today_indicator.get_rect(centerx=day_rect.centerx, bottom=day_rect.bottom - 5)
            screen.blit(today_indicator, indicator_rect)
        else:
            draw_text(screen, day, fonts["day"], COLORS["white"], day_rect, "center", "center")

    # Get current time for highlighting
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    current_time_str = f"{current_hour:02}:{current_minute:02}"

    # Time rows and schedule cells
    for j, hour in enumerate(hours):
        # Hour cell
        hour_rect = pygame.Rect(table_x, table_y + header_height + j * row_height, time_column_width, row_height)
        pygame.draw.rect(screen, COLORS["light"], hour_rect, 0)
        pygame.draw.rect(screen, COLORS["border"], hour_rect, 1)
        draw_text(screen, hour, fonts["hour"], COLORS["text_primary"], hour_rect, "center", "center")

        # Highlight current hour
        hour_val = int(hour.split(":")[0])
        if hour_val == current_hour:
            pygame.draw.rect(screen, COLORS["highlight"], hour_rect, 6)

        # Schedule cells for each day
        for i, day in enumerate(days):
            cell_rect = pygame.Rect(table_x + time_column_width + i * column_width,
                                  table_y + header_height + j * row_height,
                                  column_width, row_height)

            try:
                cell_data = ders_programi[day][hour]
                status = cell_data["durum"]

                if status == "Boş":
                    # Available cell with gradient
                    draw_gradient_rect(screen, COLORS["available"], lighten_color(COLORS["available"]), cell_rect)
                    
                    # Draw clock icon
                    clock_center = (cell_rect.left + 25, cell_rect.centery)
                    pygame.draw.circle(screen, COLORS["white"], clock_center, 12, 0)
                    pygame.draw.circle(screen, COLORS["available"], clock_center, 12, 1)
                    # Clock hands
                    pygame.draw.line(screen, COLORS["available"], clock_center, 
                                   (clock_center[0], clock_center[1] - 8), 2)
                    pygame.draw.line(screen, COLORS["available"], clock_center, 
                                   (clock_center[0] + 6, clock_center[1]), 2)
                    
                    cell_text = 'Randevuya'
                    draw_text(screen, cell_text, fonts["empty_cell"], COLORS["dark"], 
                           pygame.Rect(cell_rect.left + 40, cell_rect.top-11, cell_rect.width - 35, cell_rect.height), 
                           "left", "center")

                    cell_text2 = 'Uygun'
                    draw_text(screen, cell_text2, fonts["empty_cell"], COLORS["dark"], 
                           pygame.Rect(cell_rect.left + 40, cell_rect.top+11, cell_rect.width - 35, cell_rect.height), 
                           "left", "center")
                else:
                   # Unavailable cell with gradient
                    draw_gradient_rect(screen, COLORS["unavailable"], lighten_color(COLORS["unavailable"]), cell_rect)

                    entries = cell_data.get("entries", [{"aktivite": cell_data["aktivite"], "düzenleyen": cell_data["düzenleyen"]}])
                    cell_key = f"{day}_{hour}"

                    # Initialize scroll index if not exists
                    if cell_key not in scroll_indices:
                        scroll_indices[cell_key] = 0

                    # Safely cycle through entries
                    index = scroll_indices[cell_key] % len(entries)
                    current_entry = entries[index]
                    if display_mode == "info":
                        aktivite = current_entry["aktivite"]
                        duzenleyen = current_entry["düzenleyen"]
                    else:
                        aktivite = hour  # like "10:00"
                        duzenleyen = day  # like "Cuma"

                    print(f"DRAWING MODE: {display_mode} — {aktivite} / {duzenleyen}")

                    # Add separator line
                    pygame.draw.line(screen, COLORS["white"], 
                                   (cell_rect.left + 10, cell_rect.centery),
                                   (cell_rect.right - 10, cell_rect.centery), 1)
                    
                    # Activity name with icon
                    activity_rect = pygame.Rect(cell_rect.x + 5, cell_rect.y + 5,
                                              cell_rect.width - 10, cell_rect.height // 2 - 5)
                    draw_text(screen, aktivite, fonts["cell"], COLORS["white"], activity_rect, "center", "center")
                    
                    # Organizer name with smaller font and icon
                    organizer_rect = pygame.Rect(cell_rect.x + 5, cell_rect.centery + 5,
                                               cell_rect.width - 10, cell_rect.height // 2 - 10)
                    
                    # Person icon (simplified)
                    icon_x = cell_rect.x + 20
                    icon_y = cell_rect.centery + organizer_rect.height // 2
                    pygame.draw.circle(screen, COLORS["white"], (icon_x, icon_y - 5), 5, 1)
                    pygame.draw.line(screen, COLORS["white"], (icon_x, icon_y), (icon_x, icon_y + 8), 1)
                    
                    draw_text(screen, duzenleyen, fonts["cell_small"], COLORS["white"], 
                           pygame.Rect(icon_x + 15, organizer_rect.y, organizer_rect.width - 25, organizer_rect.height), 
                           "left", "center")

                # Cell border (subtle)
                pygame.draw.rect(screen, COLORS["border"], cell_rect, 1)

            except KeyError:
                # Empty cell
                pygame.draw.rect(screen, COLORS["light"], cell_rect, 0)
                pygame.draw.rect(screen, COLORS["border"], cell_rect, 1)
                draw_text(screen, "Veri Yok", fonts["cell_small"], COLORS["text_secondary"], cell_rect, "center", "center")

# QR kod bilgi kartını çiz
def draw_qr_info_card(screen, fonts, qr_surface, room_name):
    if qr_surface is None:
        return
    
    # Calculate card dimensions
    card_width = qr_surface.get_width() + 60
    card_height = qr_surface.get_height() + 170
    card_x = 20
    card_y = 20
    
    # Draw card background with shadow
    card_shadow = pygame.Surface((card_width + 10, card_height + 10), pygame.SRCALPHA)
    card_shadow.fill((0, 0, 0, 30))
    screen.blit(card_shadow, (card_x + 5, card_y + 5))
    
    pygame.draw.rect(screen, COLORS["light"], (card_x, card_y, card_width, card_height), 0)
    
    # Card header with gradient
    header_height = 50
    header_rect = pygame.Rect(card_x, card_y, card_width, header_height)
    draw_gradient_rect(screen, COLORS["primary"], darken_color(COLORS["primary"]), header_rect)
    
    # Header text
    draw_text(screen, "Odaya Erişim", fonts["subtitle"], COLORS["white"], header_rect, "center", "center")
    
    # QR code
    qr_x = card_x + (card_width - qr_surface.get_width()) // 2
    qr_y = card_y + header_height + 10
    screen.blit(qr_surface, (qr_x, qr_y))
    
    # Add instructions text
    instruction_rect = pygame.Rect(card_x + 10, qr_y + qr_surface.get_height() + 10, 
                                card_width - 20, 30)
    draw_text(screen, "QR Kodu Uygulamadan Taratın", fonts["info"], COLORS["text_primary"], 
           instruction_rect, "center", "center")
    
    # Room name with icon
    room_rect = pygame.Rect(card_x + 10, instruction_rect.bottom + 10, card_width - 20, 40)
    
    # Draw room icon (simple house)
    icon_x = room_rect.left + 30
    icon_y = room_rect.centery
    pygame.draw.polygon(screen, COLORS["primary"], 
                      [(icon_x, icon_y - 10), (icon_x + 15, icon_y - 20), (icon_x + 30, icon_y - 10)])
    pygame.draw.rect(screen, COLORS["primary"], (icon_x + 5, icon_y - 10, 20, 20))
    
    # Room name with bold font
    room_text_rect = pygame.Rect(icon_x + 40, room_rect.top, room_rect.width - 70, room_rect.height)
    draw_text(screen, room_name, fonts["subtitle"], COLORS["primary"], room_text_rect, "left", "center")

# Alt bilgi çiz
def draw_footer(screen, fonts):
    footer_height = 70
    footer_rect = pygame.Rect(0, screen_height - footer_height, screen_width, footer_height)
    
    # Gradient background for footer
    draw_gradient_rect(screen, darken_color(COLORS["primary"]), COLORS["primary"], footer_rect)
    
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M:%S")
    
    # Date and time with icons
    date_time_str = f"{date_str} • {time_str}"
    date_time_rect = pygame.Rect(screen_width -380, screen_height - footer_height, 200, footer_height)
    
    # Clock icon (simple circle with hands)
    clock_x = date_time_rect.left
    clock_y = date_time_rect.centery
    pygame.draw.circle(screen, COLORS["light"], (clock_x, clock_y), 15, 2)
    pygame.draw.line(screen, COLORS["light"], (clock_x, clock_y), (clock_x, clock_y - 5), 2)
    pygame.draw.line(screen, COLORS["light"], (clock_x, clock_y), (clock_x + 4, clock_y), 2)
    
    draw_text(screen, date_time_str, fonts["footer"], COLORS["light"], 
           pygame.Rect(clock_x + 20, date_time_rect.top, date_time_rect.width - 15, date_time_rect.height), 
           "left", "center")
    
    # App info with logo/icon
    app_info = "Oda Rezervasyon Sistemi"
    app_info_rect = pygame.Rect(20, screen_height - footer_height, 300, footer_height)
    
    # App logo (simple calendar icon)
    logo_x = app_info_rect.left + 10
    logo_y = app_info_rect.centery
    pygame.draw.rect(screen, COLORS["light"], (logo_x, logo_y - 8, 16, 16), 1, 2)
    pygame.draw.line(screen, COLORS["light"], (logo_x + 4, logo_y - 12), (logo_x + 4, logo_y - 4), 1)
    pygame.draw.line(screen, COLORS["light"], (logo_x + 12, logo_y - 12), (logo_x + 12, logo_y - 4), 1)
    
    draw_text(screen, app_info, fonts["footer"], COLORS["light"], 
           pygame.Rect(logo_x + 25, app_info_rect.top, app_info_rect.width - 25, app_info_rect.height), 
           "left", "center")

def draw_gradient_rect(screen, color1, color2, rect, border_radius=0, top_only=False):
    if top_only:
        # Gradient only from top to middle
        h_factor = 0.5
    else:
        # Full gradient
        h_factor = 1.0
        
    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    
    for y in range(int(rect.height * h_factor)):
        factor = y / (rect.height * h_factor)
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        pygame.draw.line(surface, (r, g, b), (0, y), (rect.width, y))
    
    if top_only:
        # Fill the bottom part with color2
        pygame.draw.rect(surface, color2, (0, int(rect.height * h_factor), rect.width, int(rect.height * (1 - h_factor))))
    
    # Apply border radius if specified
    if border_radius > 0:
        # Create a mask surface with rounded corners
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, rect.height), 0, border_radius)
        
        # Apply the mask (for newer Pygame versions)
        try:
            surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        except:
            # Fallback for older Pygame versions
            # Just use the gradient without rounded corners
            pass
    
    screen.blit(surface, rect)

def darken_color(color, factor=0.7):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

def lighten_color(color, factor=0.3):
    return (min(255, int(color[0] + (255 - color[0]) * factor)),
           min(255, int(color[1] + (255 - color[1]) * factor)),
           min(255, int(color[2] + (255 - color[2]) * factor)))


def fetch_qr_token():
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 300000  # 300000 saniye içinde geçersiz olacak
        },
        jwtsecret,
        algorithm="HS256"
    )
    url = f"http://{raspberryNodeip}/getQRCodeToken"
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

def draw_text(screen, text, font, color, rect, align_x="left", align_y="top"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if align_x == "center":
        text_rect.centerx = rect.centerx
    elif align_x == "right":
        text_rect.right = rect.right
    else:
        text_rect.left = rect.left
    
    if align_y == "center":
        text_rect.centery = rect.centery
    elif align_y == "bottom":
        text_rect.bottom = rect.bottom
    else:
        text_rect.top = rect.top
    
    screen.blit(text_surface, text_rect)

def fetch_schedule_data():
    encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 300000  # 300000 saniye içinde geçersiz olacak
        },
        jwtsecret,
        algorithm="HS256"
    )
    url = f"http://{raspberryNodeip}/getSchedule"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": 1, "token": "{encoded_jwt}"}}'
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            # Parse the JSON response and get the token
            response_data = response.json()
            return response_data
        else:
            print(f"API isteği başarısız oldu. Hata kodu: {response.status_code}")
    except requests.RequestException as e:
        print(f"API bağlantı hatası: {e}")
    return None

def update_schedule_data():
    global ders_programi
    try:
        response = requests.get("http://172.18.6.111:32002/getSchedule", timeout=3)
        response.raise_for_status()
        new_data = response.json()
    except Exception as e:
        print("⚠️ API bağlantı hatası, sahte veri kullanılıyor:", e)
        new_data = {
            "schedule": [
        {
            "day": "2025-05-02T10:00:00Z",
            "hour": "10:00",
            "title": "Math",
            "username": "Ali"
        },
        {
            "day": "2025-05-02T10:00:00Z",
            "hour": "12:00",
            "title": "Science",
            "username": "Ayşe"
        }
    ]
        }

    ders_programi = transform_schedule(new_data)


# ONLY FOR DEVELOPMENT SHOULD BE DELETED WHEN USING
def handle_events():
    for event in pygame.event.get():
        if event.type == QUIT:
            return False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
    return True


# Pygame başlatma
pygame.init()
pygame.mouse.set_visible(0)
display_mode = "info"
last_display_change = pygame.time.get_ticks()
count = 1
last_count_update = pygame.time.get_ticks()
interval = 30000  # First interval: 30 seconds


# Ekran boyutunu al
screen_info = pygame.display.Info()
print(screen_info)
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Oda Rezervasyon Sistemi")

# Fontları yükle
fonts = {
    "title": pygame.font.SysFont("Arial", int(screen_height * 0.045)),  # Ekran yüksekliğinin %4'ü
    "title_small": pygame.font.SysFont("Arial", int(screen_height * 0.015)),
    "subtitle": pygame.font.SysFont("Arial", int(screen_height * 0.035)),
    "day": pygame.font.SysFont("Arial", int(screen_height * 0.03)),
    "hour": pygame.font.SysFont("Arial", int(screen_height * 0.021)),
    "empty_cell": pygame.font.SysFont("Arial", int(screen_height * 0.025)),
    "cell": pygame.font.SysFont("Arial", int(screen_height * 0.026)),
    "cell_small": pygame.font.SysFont("Arial", int(screen_height * 0.024)),
    "info": pygame.font.SysFont("Arial", int(screen_height * 0.020)),
    "footer": pygame.font.SysFont("Arial", int(screen_height * 0.033))
}

# Ana döngü
running = True
last_update_time = 0
qr_surface = None
room_name = "Örnek Oda"  # Varsayılan oda adı

clock = pygame.time.Clock()
FPS = 1  # Increased FPS for smoother animations

# İlk oda adını al
fetched_room_name = fetch_room_name()
if fetched_room_name:
    room_name = fetched_room_name

# İlk QR kodunu al
qr_token = fetch_qr_token()
if qr_token:
    qr_surface = generate_qr_code_surface(qr_token, screen_width, screen_height)

update_schedule_data()
draw_schedule_table(screen, fonts)

while running:
    clock.tick(FPS)
    
    running = handle_events()
    
    current_time = pygame.time.get_ticks()
    
    # QR kodu her dakika güncelle
    if current_time - last_update_time > 57000 or qr_surface is None:
        last_update_time = current_time
        old_qr = qr_surface
        
        # Oda adını güncelle
        fetched_room_name = fetch_room_name()
        if fetched_room_name:
            room_name = fetched_room_name
        
        # Yeni QR kodunu al
        qr_token = fetch_qr_token()
        if qr_token:
            qr_surface = generate_qr_code_surface(qr_token, screen_width, screen_height)

        # Ders Programının update et
        update_schedule_data()
    

    
    # Clear screen with gradient background
    draw_gradient_background(screen, darken_color(COLORS["background"]), COLORS["background"])
    
    # Draw components
    if qr_surface:
        draw_qr_info_card(screen, fonts, qr_surface, room_name)
    # Update scroll indices for each cell every 30 seconds
    if pygame.time.get_ticks() - last_scroll_time > 30000:  # 30 seconds
        last_scroll_time = pygame.time.get_ticks()
        for key in scroll_indices:
            day, hour = key.split("_")
            entries = ders_programi[day][hour].get("entries", [])
            if entries:
                scroll_indices[key] = (scroll_indices[key] + 1) % len(entries)

    now = pygame.time.get_ticks()

    print(now - last_count_update)
    if now - last_count_update >= interval:
        count += 1
        last_count_update = now
        interval = 10000 if interval == 30000 else 30000  # Toggle between 30s and 10s

    # Set display mode based on whether count is even or odd
    display_mode = "info" if count % 2 == 0 else "time"


    print(f"MODE: {display_mode}, TIME: {pygame.time.get_ticks() - last_display_change}")
    print(f"COUNT: {count}, MODE: {display_mode}, INTERVAL: {interval}")
    draw_schedule_table(screen, fonts)
    
    draw_footer(screen, fonts)
    
    pygame.display.flip()

pygame.quit()
