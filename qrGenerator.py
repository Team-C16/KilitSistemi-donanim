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
import re
import ast
import json

# JWT secret key
jwtsecret = "JWT_SECRET"

# Raspberry Node IP
raspberryNodeip = 'http://172.28.6.15:8001/kilitSistemi'

room_id = 2

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
    "softBackground": (0,119,204),       # soft blue
    "StartColour": (209, 96, 61),
    "grey": (211, 211, 211)
}

# :root {
# 	--zone--main-color: #3b1f2b;
# 	--zone--secondary-color: #642b36;
# 	--selection--main-color: #F0F0F0;
# 	--selection--secondary-color: #D6D6D6;
# 	--selection--hover-color: #3b82f6;
# 	--text-light: #D6D6D6;
# 	--surface: #ffffff;
# 	--surface-2: #F0F0F0;
# 	--navbar-background: white;
# 	--close-btn: #ff4d4d;
# 	--close-btn-hover: #cc0000;
# 	--text-color: black;
# 	--card-color: var(--surface-2);	
# 	--msg--text-color: black;
# 	--box-shadow: rgba(0, 0, 0, 0.1);
# 	--dashboard-primary: #3b1f2b;
# 	--dashboard-secondary: #642b36;
# 	--dashboard-accent: #8a3b48;
# 	--dashboard-light: #f5e9ec;
# 	--dashboard-medium: #e5d0d5;
# }
# 
# body.dark-mode {
# 	--zone--main-color: #8a3b48;
# 	--zone--secondary-color: #642b36;
# 	--selection--main-color: #2d2d2d;
# 	--selection--secondary-color: #3d3d3d;
# 	--selection--hover-color: #4dabf7;
# 	--text-light: #e0e0e0;
# 	--surface: #1a1a1a;
# 	--surface-2: #2d2d2d;
# 	--navbar-background: #1a1a1a;
# 	--close-btn: #ff4d4d;
# 	--close-btn-hover: #cc0000;
# 	--text-color: #ffffff;
# 	--card-color: var(--surface-2);
# 	--msg--text-color: #ffffff;
# 	--box-shadow: rgba(0, 0, 0, 0.2);
# 	--dashboard-primary: #8a3b48;
# 	--dashboard-secondary: #642b36;
# 	--dashboard-accent: #3b1f2b;
# 	--dashboard-light: #2d2d2d;
# 	--dashboard-medium: #3d3d3d;
# }

def transform_schedule(api_data):
    dict_tr = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı",
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }

    # Define the 5 days and hours you display
    start_date = datetime.now()
    days = [(start_date + timedelta(days=i)) for i in range(5)]
    hours = [f"{h:02}:00" for h in range(9, 19)]  # 09:00 to 18:00

    # Step 1: fill with all "Boş"
    ders_programi = {}
    for date_obj in days:
        weekday_tr = dict_tr[date_obj.strftime("%A")]
        if weekday_tr not in ders_programi:
            ders_programi[weekday_tr] = {}
        for hour in hours:
            ders_programi[weekday_tr][hour] = {
                "durum": "Boş",
                "aktivite": "",
                "düzenleyen": "",
                "rendezvous_id": "",
                "entries": []
            }

    # Step 2: overwrite with "Dolu" from API
    schedule = api_data.get("schedule", [])
    for entry in schedule:
        try:
            # Parse UTC datetime and add 1 day for local time
            utc_time = datetime.strptime(entry["day"], "%Y-%m-%dT%H:%M:%S.%fZ")
            local_time = utc_time + timedelta(days=1)
            date_str = local_time.strftime("%Y-%m-%d")
            weekday_tr = dict_tr[local_time.strftime("%A")]

            # Get hour in local time (keeping same hour for simplicity)
            time_str = entry["hour"].split(":")[0]  # Get "12" from "12:00:00"
            hour_str = f"{int(time_str):02d}:00"  # Format as "12:00"

            # Update the schedule
            if weekday_tr in ders_programi and hour_str in ders_programi[weekday_tr]:
                ders_programi[weekday_tr][hour_str] = {
                    "durum": "Dolu",
                    "aktivite": entry["title"],
                    "düzenleyen": entry["fullName"],
                    "rendezvous_id":  entry["rendezvous_id"],
                    "entries": [{
                        "aktivite": entry["title"],
                        "users": [entry["fullName"]],
                        "time": hour_str,
                        "day": date_str
                    }]
                }
            
        except Exception as e:
            print("⚠️ Error processing entry:", entry, "Error:", e)

    return ders_programi



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
    url = f"{raspberryNodeip}/getQRCodeToken"
    print(url)
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "room_name": 1}}'
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

                    aktivite = ders_programi[day][hour].get("aktivite")
    
                    duzenleyen = ders_programi[day][hour].get("düzenleyen")
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
    url = f"{raspberryNodeip}/getQRCodeToken"
    headers = {"Content-Type": "application/json"}
    data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}"}}'
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
    text_surface = font.render(str(text), True, color)
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

def fetch_details_data(rendezvous_id): # Added parameters for clarity
    """
    Fetches schedule details from the Node.js API endpoint.
    Handles JWT encoding, network requests, and basic error handling.
    """
    if not jwtsecret:
        print("Error: JWT secret is not defined.")
        return None
    if not raspberryNodeip:
        print("Error: Raspberry Pi Node IP is not defined.")
        return None

    try:
        # 1. Encode JWT
        encoded_jwt = jwt.encode(
            {
                "exp": time.time() + 300 # Token invalid after 5 minutes (300 seconds)
                # You might also add 'iat' (issued at) and 'sub' (subject) claims
            },
            jwtsecret,
            algorithm="HS256"
        )

        # 2. Construct URL and Payload (using dictionary for data, then json.dumps)
        url = f"{raspberryNodeip}/getScheduleDetails"
        headers = {"Content-Type": "application/json"}
        
        # FIX Problem 5: Use the `room_id` parameter dynamically
        payload = {
            "room_id": room_id, # Use the passed room_id
            "token": encoded_jwt,
            "rendezvous_id": rendezvous_id
        }

        # 3. Make the Request with Timeout and Error Handling
        print(f"DEBUG: Requesting {url} with rendezvous_id={rendezvous_id}, room_id={room_id}")
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10) # FIX Problem 2: Added 10-second timeout

        # Raise an HTTPError for bad responses (4xx or 5xx status codes)
        response.raise_for_status() 

        # FIX Problem 3: Attempt to parse JSON only after successful status code
        response_data = response.json()
        print(f"DEBUG: API response for {rendezvous_id}: {response_data}")
        return response_data

    # FIX Problem 4: Catch all Request exceptions (network errors, timeouts, etc.)
    except requests.exceptions.Timeout:
        print(f"API request timed out for rendezvous_id {rendezvous_id} ({url}).")
        return None
    except requests.exceptions.ConnectionError:
        print(f"API connection error for rendezvous_id {rendezvous_id} ({url}). Is the server running and reachable?")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"API HTTP error for rendezvous_id {rendezvous_id}: {e.response.status_code} - {e.response.text}")
        return {"error": e.response.text} # Return error info for higher-level handling
    except json.JSONDecodeError:
        print(f"API response for rendezvous_id {rendezvous_id} was not valid JSON: {response.text}")
        return {"error": "Invalid JSON response from API"}
    except Exception as e:
        print(f"An unexpected error occurred during API request for rendezvous_id {rendezvous_id}: {e}")
        return None


def update_data():
    global ders_programi
    try:
        encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 300000  # 300000 saniye içinde geçersiz olacak
        },
        jwtsecret,
        algorithm="HS256"
        )
        payload = {
            "room_id": room_id,
            "token": encoded_jwt
        }

        response = requests.post(f"{raspberryNodeip}/getSchedule", json=payload,
                               timeout=3)
        response.raise_for_status()

        api_response = response.json()
        if isinstance(api_response, list) and len(api_response) > 0:
            new_data = api_response[0]  # Take first item if it's a non-empty list
        elif isinstance(api_response, dict):
            new_data = api_response  # Use directly if it's a dictionary
        else:
            raise ValueError("API returned invalid data format (expected list or dict)")

        print(new_data)

    except Exception as e:
        print("⚠️ API bağlantı hatası, sahte veri kullanılıyor:", e)
        # Fallback data
        new_data = {
            "schedule": [
                {
                    "title": "Toplantı",
                    "users": ["kerem", "abdulrahman", "enes"],
                    "time": "15:00",
                    "day": "2025-06-19T15:00:00.000Z",
                    "organizer": "kerem",
                    "description": """The wind carried whispers of forgotten tales across the quiet field.
                    A single crow circled above, its cry sharp against the fading light.
                    Below, shadows stretched long, reaching like fingers across the earth.
                    Somewhere in the distance, a door creaked open with no one near.
                    The evening held its breath, waiting for something unnamed."""
                },
                {
                    "title": "Sunum",
                    "users": ["ayşe", "mehmet","marvan"],
                    "time": "16:00",
                    "day": "2025-06-19T16:00:00.000Z",
                    "organizer": "marvan",
                    "description": """The wind carried whispers of forgotten tales across the quiet field.
                    A single crow circled above, its cry sharp against the fading light.
                    Below, shadows stretched long, reaching like fingers across the earth.
                    Somewhere in the distance, a door creaked open with no one near.
                    The evening held its breath, waiting for something unnamed."""
                }
            ]
        }

    global api_data
    api_data = new_data
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

def is_meeting_happening_now(meeting):
    try:
        now = datetime.now()
        meeting_day = datetime.strptime(meeting["day"], "%Y-%m-%d").date()
        start_str, end_str = meeting["time"].split("-")
        start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
        end_time = datetime.strptime(end_str.strip(), "%H:%M").time()

        start_datetime = datetime.combine(meeting_day, start_time)
        end_datetime = datetime.combine(meeting_day, end_time)

        return start_datetime <= now <= end_datetime

    except Exception as e:
        print("Time check failed:", e)
        return False


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return lines


def draw_meeting_details(screen, fonts, current_meeting, qr_code_img, room_icon, room_text):

    # Draw QR and room info (like in grid view)
    if qr_code_img:
        room_name = current_meeting.get("room_name", "Toplantı Odası")
        draw_qr_info_card(screen, fonts, qr_code_img, room_name)


    if current_meeting:
        title = current_meeting.get("title", "Başlıksız Toplantı")
        time_str = current_meeting.get("time", "Zaman Yok")
        participants_list = current_meeting.get("users", [])
        description = current_meeting.get("description", "")
        participants = current_meeting.get("users", "Belirtilmemiş")


        # Title
        title_font = fonts['bold_large']
        screen.blit(title_font.render("Toplantı başlığı: " + title, True, (0, 0, 0)), (screen_width * 0.40, 70))
        pygame.draw.line(screen, (0, 0, 0), (screen_width * 0.40, 115), (900, 115), 3)

        # Time
        screen.blit(fonts['regular'].render("Zaman: " + time_str, True, (0, 0, 0)), (screen_width * 0.40, 120))

        # Participants
        participants_list = current_meeting.get("users", [])
        participants = ", ".join(participants_list) if participants_list else "Belirtilmemiş"
        screen.blit(fonts['regular'].render("Katılımcılar: " + participants, True, (0, 0, 0)), (screen_width * 0.40, 150))


        # Description
        wrapped_lines = wrap_text(description, fonts['regular'], 900 - 250)
        print("📜 Wrapped description lines:", wrapped_lines)
        y = 180
        screen.blit(fonts['bold'].render("Toplantı Açıklaması:", True, (0, 0, 0)), (screen_width * 0.40, y))
        y += 30
        for line in wrapped_lines:
            screen.blit(fonts['regular'].render(line, True, (0, 0, 0)), (screen_width * 0.40, y))
            y += 25

def get_date_from_day_name(tr_day_name):
    tr_to_eng = {
        "Pazartesi": "Monday",
        "Salı": "Tuesday",
        "Çarşamba": "Wednesday",
        "Perşembe": "Thursday",
        "Cuma": "Friday",
        "Cumartesi": "Saturday",
        "Pazar": "Sunday"
    }
    today = datetime.now()
    for i in range(5):  # Only check the next 5 days
        date = today + timedelta(days=i)
        if date.strftime("%A") == tr_to_eng[tr_day_name]:
            return date.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")  # fallback


# Pygame başlatma
pygame.init()
pygame.mouse.set_visible(0)
last_count_update = pygame.time.get_ticks()
last_switch_time = pygame.time.get_ticks()

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
    "footer": pygame.font.SysFont("Arial", int(screen_height * 0.033)),
    "bold": pygame.font.SysFont("Arial", int(screen_height * 0.026), bold=True),
    "bold_large": pygame.font.SysFont("Arial", int(screen_height * 0.045), bold=True),
    "regular": pygame.font.SysFont("Arial", int(screen_height * 0.026))
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



update_data()
draw_schedule_table(screen, fonts)

room_text = fonts['bold'].render("Toplantı Odası 101", True, (0, 0, 0))
times = 0

# ... (initializations of other variables like display_mode, last_switch_time, etc.)

meetings = [] # <-- This should be the ONLY place 'meetings' is initialized to an empty list
current_meeting = None # Initialize current_meeting here too

while running:    
    if times == 0:
        display_mode = "grid"
        times += 1
        
    clock.tick(1)

    
    current_time = pygame.time.get_ticks() # This is 'now'

    # QR kodu her dakika güncelle
    if current_time - last_update_time > 57000 or qr_surface is None:
        last_update_time = current_time
        old_qr = qr_surface # Still unused, can remove
        
        # Oda adını güncelle
        fetched_room_name = fetch_room_name()
        if fetched_room_name:
            room_name = fetched_room_name
        
        # Yeni QR kodunu al
        qr_token = fetch_qr_token()
        if qr_token:
            qr_surface = generate_qr_code_surface(qr_token, screen_width, screen_height)

        # Ders Programını update et
        update_data() # This should update `ders_programi`

    # Clear screen with gradient background
    draw_gradient_background(screen, darken_color(COLORS["background"]), COLORS["background"])
    
    # Draw components (main room QR card)
    if qr_surface:
        draw_qr_info_card(screen, fonts, qr_surface, room_name)

    print(f"Display mode: {display_mode}, Time since last switch: {pygame.time.get_ticks() - last_switch_time}")
    
    # Update scroll indices every 30 seconds
    if pygame.time.get_ticks() - last_scroll_time > 10000:
        last_scroll_time = pygame.time.get_ticks()
        for key in scroll_indices:
            day, hour = key.split("_")
            # Add safety checks for dictionary keys
            if day in ders_programi and hour in ders_programi[day]:
                entries = ders_programi[day][hour].get("entries", [])
                if entries:
                    scroll_indices[key] = (scroll_indices[key] + 1) % len(entries)


    draw_footer(screen, fonts) 
    
    # === CRITICAL FIX for `meetings` list management ===
    # meetings = [] # <--- REMOVE THIS LINE FROM INSIDE THE LOOP
    now = pygame.time.get_ticks() # This is 'current_time'

    # Flag to break outer loop once a current meeting is found
    found_current_meeting_this_cycle = False

    if display_mode == "grid" and now - last_switch_time > 30000:
        # Clear meetings *before* repopulating it only when entering this block
        meetings.clear() # Or meetings = [] if you prefer a new list instance
        
        for day, hours in ders_programi.items():
            for hour, entry in hours.items():
                if entry["durum"] == "Dolu" and entry.get("rendezvous_id"):
                    rendezvous_id = entry["rendezvous_id"]

                    # Assuming fetch_details_data handles token globally
                    data = fetch_details_data(rendezvous_id)
                    if data:
                        # Handle API errors that might be returned in the 'data' dictionary
                        if isinstance(data, dict) and data.get("error"):
                            print(f"API error for rendezvous_id {rendezvous_id}: {data['error']}")
                            continue # Skip to the next entry in ders_programi

                        main_data = None
                        group_members = []
                        details = None

                        # First, try to get data assuming it's a dictionary with 'dataResult' and 'groupResult'
                        if isinstance(data, dict):
                            main_data = data.get("dataResult")
                            group_members = data.get("groupResult", [])
                            
                            # If 'dataResult' is found and is a non-empty list, use its first element
                            if main_data and isinstance(main_data, list) and len(main_data) > 0:
                                details = main_data[0]
                            # else: if data is a dict but no dataResult, maybe it's just the details directly?
                            # This case is less clear, but if your API sometimes returns a dict that *is* the detail
                            # for a single meeting, you might need another check here.
                            # For now, let's assume if it's a dict, it's either `dataResult` or an error.

                        # Second, if 'data' itself is a list, treat it as the main data
                        elif isinstance(data, list) and len(data) > 0:
                            details = data[0]
                            # In this case, there's no `groupResult` key, so group_members remains an empty list by default.
                            # This matches your previous logic for this scenario.
                        
                        # Now, with 'details' potentially populated from either format, proceed
                        if details: # Only proceed if details were successfully extracted from either format
                            users = []
                            # isGroup check should be on 'details', not 'data'
                            if details.get("isGroup") in [0, 1] and group_members: # `group_members` comes from the dict case
                                users = [member["fullName"] for member in group_members]
                            else:
                                users = [details.get("fullName")] if details.get("fullName") else []

                            meeting_info = {
                                "rendezvous_id": rendezvous_id,
                                "day": get_date_from_day_name(day),
                                "time": f"{hour}-{int(hour[:2])+1:02d}:00",
                                "title": details.get("title", entry["aktivite"]),
                                "organizer": details.get("fullName", entry["düzenleyen"]),
                                "users": users,
                                "description": details.get("message", ""),
                                "room_name": {room_name}
                            }
                            meetings.append(meeting_info)

                            if is_meeting_happening_now(meeting_info): 
                                display_mode = "detail"
                                last_switch_time = now
                                current_meeting = meeting_info
                                found_current_meeting_this_cycle = True
                                break
                        else:
                            print(f"No valid details extracted from API response for rendezvous_id {rendezvous_id}")
                    else:
                        print(f"Failed to fetch data for rendezvous_id {rendezvous_id}")
            
            # Break outer loop if flag is set
            if found_current_meeting_this_cycle:
                break


    elif display_mode == "detail" and now - last_switch_time > 10000:
            print(f"[{now}] Meeting ended or detail timeout. Switching back to grid.")
            display_mode = "grid"
            current_meeting = None # Clear current meeting data

    # Main Drawing Logic
    if display_mode == "grid":
        # Pass required arguments to `draw_schedule_table`
        draw_schedule_table(screen, fonts) 
    else: # display_mode == "detail"
        # Use rendezvous_id for QR data
        qr_data_for_detail = current_meeting.get("rendezvous_id") if current_meeting else None
        qr_code_img = generate_qr_code_surface(str(qr_data_for_detail), screen_width, screen_height) if qr_data_for_detail else None
        
        draw_gradient_background(screen,COLORS["success"], COLORS["info"]) 
        
        detail_rect = pygame.Rect(screen_width * 0.35, 20, screen_width * 0.5, 500)
        draw_gradient_rect(screen, COLORS["light"], COLORS["grey"], detail_rect, 30)
        
        draw_meeting_details(screen, fonts, current_meeting, qr_code_img, None, None)
        
        # draw_footer(screen, fonts)
        # draw_qr_info_card(screen, fonts, qr_surface, room_name)

    # These drawing calls should be outside the if/else for display_mode if they are always present
    # Move these outside the display_mode conditional
    draw_footer(screen, fonts) # Only call once at the end
    if qr_surface: # Only draw if qr_surface exists
        draw_qr_info_card(screen, fonts, qr_surface, room_name)


    pygame.display.flip()

pygame.quit()
