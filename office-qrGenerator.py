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
time_suffix = ":30" # Varsayılan değer, API'den çekilemezse kullanılır
# Raspberry Node IP
raspberryNodeip = 'https://pve.izu.edu.tr/randevu'

room_id = 13

accessType = 1

scroll_indices = {}
last_scroll_time = 0


# Renk Paleti (Modern, Flat UI)
COLORS = {
    "background": (245, 248, 255),      # Slightly blue-tinted background
    "primary": (51, 100, 138),           # Richer blue for primary elements
    "secondary": (72, 101, 129),        # Deep blue-gray
    "success": (46, 204, 113),          # Vibrant green
    "danger": (231, 76, 60),            # Softer red
    "warning": (241, 196, 15),          # Golden yellow
    "info": (52, 152, 219),             # Bright blue
    "light": (255, 255, 255),           # Pure white
    "dark": (44, 62, 80),               # Deep blue-gray
    "white": (255, 255, 255),           # White
    "text_primary": (0,0,0),       # Dark blue-gray text 44, 62, 80
    "text_secondary": (127, 140, 141),  # Medium gray text
    "available": (134, 187, 216),       # Vibrant green for available
    "unavailable": (142, 65, 98),       # Softer red for unavailable
    "border": (214, 219, 233),          # Subtle border color
    "highlight": (241, 196, 15),        # Highlight color
    "softBackground": (0,119,204),      # soft blue
    "StartColour": (209, 96, 61),
    "grey": (211, 211, 211),
    "black": (0,0,0),
    "Charcoal": (47, 72, 88), # org_clr 1
    "Lapis-Lazuli": (51, 100, 138), # org_clr 2
    "Carolina-blue" : (134, 187, 216), # org_clr 3
    "Magenta": (142, 65, 98), # org_clr 4
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

    # Determine display week: if today is Sat/Sun show next week's Mon-Fri,
    # otherwise show current week's Mon-Fri
    today_date = datetime.now().date()
    if today_date.weekday() >= 5:  # Sat(5), Sun(6)
        monday = today_date + timedelta(days=(7 - today_date.weekday()))
    else:
        monday = today_date - timedelta(days=today_date.weekday())

    display_start = monday
    display_end = monday + timedelta(days=4)
    display_start = monday
    days = [datetime.combine(display_start + timedelta(days=i), datetime.min.time()) for i in range(5)]
    # Build 5 weekdays (Mon-Fri)
    days = [datetime.combine(display_start + timedelta(days=i), datetime.min.time()) for i in range(5)]
    hours = [f"{h:02}{time_suffix}" for h in range(9, 19)]

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
            # Parse possible ISO formats robustly
            day_str = entry.get("day", "")
            # remove fractional seconds / Z if present
            day_clean = re.sub(r'\.\d+Z?$','', day_str)
            utc_time = datetime.strptime(day_clean, "%Y-%m-%dT%H:%M:%S")
            # Keep UTC -> convert to local date if needed (here we use utc_time.date())
            local_date = (utc_time).date() + timedelta(days=1)
            if not (display_start <= local_date <= display_end):
                continue

            weekday_tr = dict_tr[local_date.strftime("%A")]


            # Get hour string from entry if present, fallback to utc_time hour
            # DEĞİŞİKLİK 3 ve 4: Saat formatını dinamik yap
            if "hour" in entry and isinstance(entry["hour"], str) and ":" in entry["hour"]:
                time_str = entry["hour"].split(":")[0]
                hour_str = f"{int(time_str):02d}{time_suffix}"
            else:
                hour_str = f"{utc_time.hour:02d}{time_suffix}"

            # Only accept entries that fall inside our displayed Mon-Fri set
            if weekday_tr in ders_programi and hour_str in ders_programi[weekday_tr]:
                ders_programi[weekday_tr][hour_str] = {
                    "durum": "Dolu",
                    "aktivite": entry.get("title",""),
                    "düzenleyen": entry.get("fullName",""),
                    "rendezvous_id": entry.get("rendezvous_id",""),
                    "entries": [{
                        "aktivite": entry.get("title",""),
                        "users": [entry.get("fullName","")],
                        "time": hour_str,
                        "day": local_date.strftime("%Y-%m-%d")
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

def draw_rounded_rect_with_shadow(surface, rect, color, border_color, border_width, radius, shadow_offset, shadow_color):
    """ Helper function to draw a card with shadow and border. """
    shadow_rect = rect.move(shadow_offset)
    pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)


def draw_meeting_details_v2(screen, fonts, current_meeting):
    """
    Yeniden tasarlanmış, modern ve kullanıcı dostu toplantı detayları ekranı.
    """
    if not current_meeting:
        return

    # --- 1. Verileri ve Temel Ayarları Hazırla ---
    title = current_meeting.get("title", "Başlıksız Toplantı")
    time_str = current_meeting.get("time", "Zaman Belirtilmemiş")
    description = current_meeting.get("description", "Açıklama bulunmuyor.")
    participants = current_meeting.get("users", [])
    
    padding = 30
    
    # --- 2. Ana Panel (Kart) Konumlandırması ---
    # Sol Panel: Toplantı Detayları
    details_panel_rect = pygame.Rect(
        padding * 2,
        padding * 2,
        screen_width * 0.6 - (padding * 3),
        screen_height - (padding * 4) - 70 # 70 for footer
    )
    
    # Sağ Panel: Katılımcılar
    participants_panel_rect = pygame.Rect(
        details_panel_rect.right + padding,
        padding * 2,
        screen_width * 0.4 - (padding * 3),
        screen_height - (padding * 4) - 70 # 70 for footer
    )

    # --- 3. Panelleri (Kartları) Ekrana Çiz ---
    draw_rounded_rect_with_shadow(
        screen, details_panel_rect, COLORS["light"], COLORS["border"], 2, 20, (5, 5), (0, 0, 0, 40)
    )
    draw_rounded_rect_with_shadow(
        screen, participants_panel_rect, COLORS["light"], COLORS["border"], 2, 20, (5, 5), (0, 0, 0, 40)
    )

    # --- 4. Sol Paneli (Toplantı Detayları) Doldur ---
    content_x = details_panel_rect.x + padding
    current_y = details_panel_rect.y + padding

    # Başlık
    title_surface = fonts['bold_large'].render(title, True, COLORS["text_primary"])
    screen.blit(title_surface, (content_x, current_y))
    current_y += title_surface.get_height() + 10

    # Saat Bilgisi (İkon ile)
    clock_icon_pos = (content_x, current_y + 8)
    pygame.draw.circle(screen, COLORS["secondary"], clock_icon_pos, 10, 2)
    pygame.draw.line(screen, COLORS["secondary"], clock_icon_pos, (clock_icon_pos[0], clock_icon_pos[1] - 5), 2)
    pygame.draw.line(screen, COLORS["secondary"], clock_icon_pos, (clock_icon_pos[0] + 4, clock_icon_pos[1]), 2)
    
    time_surface = fonts['regular'].render(time_str, True, COLORS["text_secondary"])
    screen.blit(time_surface, (content_x + 25, current_y))
    current_y += time_surface.get_height() + 25
    
    # Ayırıcı Çizgi
    pygame.draw.line(screen, COLORS["border"], (content_x, current_y), (details_panel_rect.right - padding, current_y), 2)
    current_y += 20
    
    # Açıklama
    desc_title_surface = fonts['bold'].render("Açıklama", True, COLORS["text_primary"])
    screen.blit(desc_title_surface, (content_x, current_y))
    current_y += desc_title_surface.get_height() + 10
    
    wrapped_lines = wrap_text(description, fonts['regular'], details_panel_rect.width - (padding * 2))
    for line in wrapped_lines:
        line_surface = fonts['regular'].render(line, True, COLORS["text_secondary"])
        screen.blit(line_surface, (content_x, current_y))
        current_y += line_surface.get_height() + 5
        if current_y > details_panel_rect.bottom - padding: # Panelin dışına taşmayı önle
            break

    # --- 5. Sağ Paneli (Katılımcılar) Doldur ---
    participant_x = participants_panel_rect.x + padding
    current_y = participants_panel_rect.y + padding

    # Panel Başlığı
    participants_title_surface = fonts['bold'].render(f"Katılımcılar ({len(participants)})", True, COLORS["text_primary"])
    screen.blit(participants_title_surface, (participant_x, current_y))
    current_y += participants_title_surface.get_height() + 15
    
    # Ayırıcı Çizgi
    pygame.draw.line(screen, COLORS["border"], (participant_x, current_y), (participants_panel_rect.right - padding, current_y), 2)
    current_y += 20
    
    # Katılımcı Listesi
    img_size = (60, 60)
    for person in participants:
        # Resim
        picture_path = person.get("picture")
        if picture_path and picture_path.strip() and picture_path != "null":
            full_url = raspberryNodeip + picture_path # Global raspberryNodeip değişkenini kullanır
            img_surface = load_image_from_url(full_url)
        else:
            img_surface = pygame.image.load("profil.jpg").convert_alpha() # Yerel fallback resim
        
        if img_surface:
            circular_img = make_circle_image(img_surface, size=img_size, border_color=COLORS["primary"], border_width=3)
            screen.blit(circular_img, (participant_x, current_y))

        # İsim
        fullName = person.get("fullName", "İsimsiz")
        name_surface = fonts['cell'].render(fullName, True, COLORS["text_secondary"])
        # Resmi ortalayacak şekilde ismi dikey olarak hizala
        name_rect = name_surface.get_rect(left=participant_x + img_size[0] + 15, centery=current_y + img_size[1] // 2)
        screen.blit(name_surface, name_rect)

        current_y += img_size[1] + 15
        if current_y > participants_panel_rect.bottom - padding: # Panelin dışına taşmayı önle
            break        

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
    data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "room_name": 1, "accessType": "{accessType}"}}'
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


def fetch_time_format_config():
    """
    Zaman formatı (örn: ':00', ':30') bilgisini API'den çeker.
    Bu fonksiyon POST metodu, room_id ve JWT token kullanır.
    """
    global time_suffix
    try:
        encoded_jwt = jwt.encode(
            {"exp": time.time() + 300000000},
            jwtsecret,
            algorithm="HS256"
        )
        
        url = f"{raspberryNodeip}/getIndexesRasp"
        payload = {
            "room_id": room_id,
            "token": encoded_jwt
        }
        
        print(f"DEBUG: İstek gönderiliyor -> {url}")
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        
        config_data = response.json()
        
        # --- İsteğiniz üzerine eklenen debug print'i ---
        print("DEBUG: /getIndexesRasp API Yanıtı:", config_data)
        # ----------------------------------------------

        for item in config_data:
            if item.get("indexName") == "hour":
                time_suffix = item.get("indexValue", ":30")
                print(f"✅ Zaman formatı API'den başarıyla alındı: '{time_suffix}'")
                return
        
        print("⚠️ 'hour' için zaman formatı API yanıtında bulunamadı. Varsayılan kullanılıyor.")

    except requests.RequestException as e:
        print(f"API bağlantı hatası (getIndexesRasp): {e}. Varsayılan zaman formatı ('{time_suffix}') kullanılacak.")
    except Exception as e:
        print(f"Bir hata oluştu (getIndexesRasp): {e}. Varsayılan zaman formatı ('{time_suffix}') kullanılacak.")

# Ders programı tablosu çizme fonksiyonu
def draw_schedule_table(screen, fonts):
    # Map English weekday names to Turkish
    week_map_en_to_tr = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı",
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }

    # Determine Monday of display week (current week or next week if weekend)
    today = datetime.now().date()
    if today.weekday() >= 5:  # Sat/Sun -> next Monday
        monday = today + timedelta(days=(7 - today.weekday()))
    else:
        monday = today - timedelta(days=today.weekday())

    # Build Monday..Friday with exact date
    days_with_dates = []
    for i in range(5):
        date_obj = monday + timedelta(days=i) 
        day_name_en = date_obj.strftime("%A")
        day_name_tr = week_map_en_to_tr.get(day_name_en, "Pazartesi")
        day_key = date_obj.strftime("%Y-%m-%d")
        days_with_dates.append((day_name_tr, day_key, date_obj))

    # All hours
    hours = [f"{h:02}{time_suffix}" for h in range(9, 19)]

    # Pre-fill missing data in ders_programi with "Boş"
    for (day_tr, date_key, date_obj) in days_with_dates:
        if day_tr not in ders_programi:
            ders_programi[day_tr] = {hour: {"durum": "Boş"} for hour in hours}
        else:
            for hour in hours:
                if hour not in ders_programi[day_tr]:
                    ders_programi[day_tr][hour] = {"durum": "Boş"}

    # Layout
    margin = screen_width // 100
    header_height = 70  # slightly taller to fit date
    row_height = screen_height // 12
    time_column_width = screen_width // 20
    column_width = screen_width // 8
    border_radius = 10

    table_width = time_column_width + len(days_with_dates) * column_width + screen_width * 0.23
    table_x = screen_width * 0.05
    table_y = 30
    column_width = (table_width - table_x) / 5

    # Table background
    table_bg_rect = pygame.Rect(table_x - 10, table_y - 10, table_width + 20,
                                header_height + len(hours) * row_height + 20)
    shadow_surface = pygame.Surface((table_bg_rect.width, table_bg_rect.height), pygame.SRCALPHA)
    shadow_surface.fill((0, 0, 0, 20))
    screen.blit(shadow_surface, (table_bg_rect.x + 5, table_bg_rect.y + 5))
    pygame.draw.rect(screen, COLORS["light"], table_bg_rect, 0, border_radius)

    # Header background
    header_rect = pygame.Rect(table_x, table_y, table_width, header_height)
    draw_gradient_rect(screen, COLORS["Lapis-Lazuli"], darken_color(COLORS["Lapis-Lazuli"]), header_rect, border_radius)

    # Time column header
    time_header_rect = pygame.Rect(table_x, table_y, time_column_width, header_height)
    pygame.draw.rect(screen, COLORS["Lapis-Lazuli"], time_header_rect, 0)
    draw_text(screen, "Saat", fonts["day"],COLORS["white"], time_header_rect, "center", "center")

    # Day headers with name + date
    today_date = datetime.now().date()
    for i, (day_tr, date_key, date_obj) in enumerate(days_with_dates):
        day_rect = pygame.Rect(table_x + time_column_width + i * column_width,
                               table_y, column_width, header_height)

        if date_obj == today_date:
            pygame.draw.rect(screen, COLORS["Carolina-blue"], day_rect, 0)

            # Day name (top)
            draw_text(screen, day_tr, fonts["day"], COLORS["black"], day_rect, "center", "top")

            # "Bugün" slightly above the bottom
            today_indicator = fonts["title_small"].render("Bugün", True, COLORS["black"])
            indicator_rect = today_indicator.get_rect(centerx=day_rect.centerx, bottom=day_rect.bottom - 25)
            screen.blit(today_indicator, indicator_rect)

            # Date directly under "Bugün"
            draw_text(screen, day_tr, fonts["day"], COLORS["black"], day_rect, "center", "top")
            draw_text(screen, date_obj.strftime("%Y-%m-%d"), fonts["cell_small"], COLORS["black"], day_rect, "center", "bottom")

        else:
            draw_text(screen, day_tr, fonts["day"], COLORS["white"], day_rect, "center", "top")
            draw_text(screen, date_obj.strftime("%Y-%m-%d"), fonts["cell_small"], COLORS["white"], day_rect, "center", "bottom")


    # Current time
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute

    # Rows
    for j, hour in enumerate(hours):
        # Hour label cell
        hour_rect = pygame.Rect(table_x, table_y + header_height + j * row_height,
                                time_column_width, row_height)
        pygame.draw.rect(screen, COLORS["Lapis-Lazuli"], hour_rect, 0)
        pygame.draw.rect(screen, COLORS["border"], hour_rect, 1)
        draw_text(screen, hour, fonts["hour"], COLORS["text_primary"], hour_rect, "center", "center")

        suffix_minute = int(time_suffix.split(':')[1])

        # 2. Vurgulanması gereken hedef saati hesapla
        target_highlight_hour = 0
        if current_minute < suffix_minute:
            target_highlight_hour = current_hour - 1 
        else:
            target_highlight_hour = current_hour
        # 3. Mevcut satırın saatini al ("14:30" -> 14)
        hour_val = int(hour.split(":")[0])

        if hour_val == target_highlight_hour:
            pygame.draw.rect(screen, COLORS["highlight"], hour_rect, 6)

        # Schedule cells
        for i, (day_tr, date_key, date_obj) in enumerate(days_with_dates):
            cell_rect = pygame.Rect(table_x + time_column_width + i * column_width,
                                    table_y + header_height + j * row_height,
                                    column_width, row_height)
            try:
                cell_data = ders_programi[day_tr][hour]
                status = cell_data.get("durum", "Boş")

                if status == "Boş":
                    draw_gradient_rect(screen, darken_color(COLORS["available"]), darken_color(COLORS["available"]), cell_rect)
                    # Clock icon
                    clock_center = (cell_rect.left + 25, cell_rect.centery)
                    pygame.draw.circle(screen, COLORS["white"], clock_center, 12, 0)
                    pygame.draw.circle(screen, COLORS["available"], clock_center, 12, 1)
                    pygame.draw.line(screen, COLORS["available"], clock_center, (clock_center[0], clock_center[1]-8), 2)
                    pygame.draw.line(screen, COLORS["available"], clock_center, (clock_center[0]+6, clock_center[1]), 2)
                    # Text
                    draw_text(screen, "Randevuya", fonts["empty_cell"], COLORS["black"],
                              pygame.Rect(cell_rect.left+40, cell_rect.top-11, cell_rect.width-35, cell_rect.height),
                              "left", "center")
                    draw_text(screen, "Uygun", fonts["empty_cell"], COLORS["black"],
                              pygame.Rect(cell_rect.left+40, cell_rect.top+11, cell_rect.width-35, cell_rect.height),
                              "left", "center")
                else:
                    draw_gradient_rect(screen, COLORS["unavailable"], lighten_color(COLORS["unavailable"]), cell_rect)
                    aktivite = cell_data.get("aktivite")
                    duzenleyen = cell_data.get("düzenleyen")
                    pygame.draw.line(screen, COLORS["white"], (cell_rect.left+10, cell_rect.centery),
                                     (cell_rect.right-10, cell_rect.centery), 1)
                    activity_rect = pygame.Rect(cell_rect.x + 5, cell_rect.y + 5,
                                                cell_rect.width - 10, cell_rect.height // 2 - 5)
                    draw_text(screen, aktivite, fonts["cell"], COLORS["white"], activity_rect, "center", "center")
                    organizer_rect = pygame.Rect(cell_rect.x + 5, cell_rect.centery + 5,
                                                 cell_rect.width - 10, cell_rect.height // 2 - 10)
                    icon_x = cell_rect.x + 20
                    icon_y = cell_rect.centery + organizer_rect.height // 2
                    pygame.draw.circle(screen, COLORS["white"], (icon_x, icon_y-5), 5, 1)
                    pygame.draw.line(screen, COLORS["white"], (icon_x, icon_y), (icon_x, icon_y + 8), 1)
                    draw_text(screen, duzenleyen, fonts["cell_small"], COLORS["white"],
                              pygame.Rect(icon_x+15, organizer_rect.y, organizer_rect.width-25, organizer_rect.height),
                              "left", "center")

                pygame.draw.rect(screen, COLORS["border"], cell_rect, 1)

            except KeyError:
                # Truly missing data
                pygame.draw.rect(screen, COLORS["light"], cell_rect, 0)
                pygame.draw.rect(screen, COLORS["border"], cell_rect, 1)
                draw_text(screen, "Veri Yok", fonts["cell_small"], COLORS["text_secondary"], cell_rect, "center", "center")

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
    app_info = "pve.izu.edu.tr/randevu"
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
    data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "accessType": "{accessType}"}}'
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

def fetch_details_data(rendezvous_id):
    if not jwtsecret or not raspberryNodeip:
        print("Missing config")
        return None

    # 💡 Define mock data here
    mock_data = {
        "3": {
            "dataResult": [{
                "title": "Toplantı",
                "message": "The golden sunlight filtered softly through the canopy of ancient trees, casting dappled shadows on the forest floor. A gentle breeze stirred the leaves, carrying with it the faint scent of wildflowers and earth. Somewhere in the distance, birds sang their melodious tunes, creating a peaceful symphony that blended perfectly with the rustling of small animals scurrying through the underbrush. It was a quiet moment of harmony, where nature’s calm seemed to embrace everything around it, inviting any passerby to pause and simply breathe.",
                "hour": "13:30",
                "fullName": "kerem",
                "picture": None,
                "isGroup": 1
            }],
            "groupResult": [
                {"fullName": "kerem yavuz", "picture": None},
                {"fullName": "Abdulrahman haffar", "picture": None},
                {"fullName": "Selim Can", "picture": None},
                {"fullName": "Hasan Ari", "picture": None},
                {"fullName": "enes halit", "picture": None},
                {"fullName": "hakan genc", "picture": None}
            ]
        },
        "6": {
           "dataResult": [{
                "title": "Toplantı",
                "message": "The golden sunlight filtered softly through the canopy of ancient trees, casting dappled shadows on the forest floor. A gentle breeze stirred the leaves, carrying with it the faint scent of wildflowers and earth. Somewhere in the distance, birds sang their melodious tunes, creating a peaceful symphony that blended perfectly with the rustling of small animals scurrying through the underbrush. It was a quiet moment of harmony, where nature’s calm seemed to embrace everything around it, inviting any passerby to pause and simply breathe.",
                "hour": "17:30",
                "fullName": "kerem",
                "picture": None,
                "isGroup": 1
            }],
            "groupResult": [
                {"fullName": "kerem yavuz", "picture": None},
                {"fullName": "Abdulrahman haffar", "picture": None},
                {"fullName": "Selim Can", "picture": None},
                {"fullName": "Hasan Ari", "picture": None},
                {"fullName": "enes halit", "picture": None},
                {"fullName": "hakan genc", "picture": None}
            ]
        }
    }

    try:
        encoded_jwt = jwt.encode(
            {"exp": time.time() + 3000000},
            jwtsecret,
            algorithm="HS256"
        )

        url = f"{raspberryNodeip}/getScheduleDetails"
        headers = {"Content-Type": "application/json"}
        payload = {
            "room_id": room_id,
            "token": encoded_jwt,
            "rendezvous_id": rendezvous_id
        }

        print(f"DEBUG: Requesting {url} with rendezvous_id={rendezvous_id}, room_id={room_id}")
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        response_data = response.json()
        print(f"DEBUG: API response for {rendezvous_id}: {response_data}")
        return response_data

    except Exception as e:
        print(f"⚠️ API failed for rendezvous_id {rendezvous_id}, using mock if available. Error: {e}")

        # ✅ Return mock data fallback
        return mock_data.get(str(rendezvous_id), None)

 

def update_data():
    global ders_programi
    try:
        encoded_jwt = jwt.encode(
        {
            "exp": time.time() + 30  # 30 saniye içinde geçersiz olacak
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
                    "users": [{  "fullName": "kerem yavuz",
                                "picture": None},
                                {"fullName": "Abdulrahman haffar",
                                "picture": None},
                                {"fullName": "Selim Can",
                                "picture": None},
                                {"fullName": "Hasan Ari",
                                "picture": None},
                                {"fullName": "enes halit",
                                "picture": None},
                                {"fullName": "hakan genc",
                                "picture": None}],
                    "hour": "13:30",
                    "day": "2025-10-02T13:00:00.000Z",
                    "fullName": "kerem",
                    "rendezvous_id": "3",
                    "description": """The wind carried whispers of forgotten tales across the quiet field.
                    A single crow circled above, its cry sharp against the fading light.
                    Below, shadows stretched long, reaching like fingers across the earth.
                    Somewhere in the distance, a door creaked open with no one near.
                    The evening held its breath, waiting for something unnamed."""
                },
                {
                    "title": "Sunum",
                    "users": ["ayşe", "mehmet","burak","serdar", "cevat"],
                    "hour": "17:30",
                    "day": "2025-10-06T17:00:00.000Z",
                    "fullName": "marvan",
                    "rendezvous_id": "6",
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

def check_if_slot_is_current(day_name, hour_str, time_suffix):
    """
    Verilen gün adı ve saat diliminin şu anki zamana denk gelip gelmediğini kontrol eder.
    API çağrısı yapmadan önce kullanılır.
    """
    try:
        now = datetime.now()
        today_name = now.strftime('%A') # Örn: 'Wednesday'

        # Türkçe gün adlarını İngilizce'ye çevirerek karşılaştırma
        gun_map = {
            "Pazartesi": "Monday", "Salı": "Tuesday", "Çarşamba": "Wednesday",
            "Perşembe": "Thursday", "Cuma": "Friday", "Cumartesi": "Saturday", "Pazar": "Sunday"
        }

        # Eğer gün adı Türkçe ise İngilizce'ye çevir, değilse olduğu gibi kullan
        english_day_name = gun_map.get(day_name, day_name)
        
        # Sadece bugünün toplantılarını kontrol et
        if english_day_name != today_name:
            return False

        # Zaman aralığını oluştur ("14:30" -> 14:30 - 15:30)
        start_hour = int(hour_str.split(':')[0])
        start_minute = int(hour_str.split(':')[1])
        
        # Bitiş saati, başlangıçtan bir saat sonrası olarak hesaplanıyor
        # time_suffix'e göre bu mantığı değiştirebilirsiniz
        # Örn: Eğer yarım saatlik dilimlerse end_minute = start_minute + 30
        end_hour = start_hour + 1
        end_minute = start_minute
        
        start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        return start_time <= now < end_time
    except Exception as e:
        print(f"Error in check_if_slot_is_current: {e}")
        return False


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            # Word too long to fit in the current line
            if current_line:
                lines.append(current_line)
            # Check if word fits alone or needs breaking
            if font.size(word)[0] <= max_width:
                current_line = word
            else:
                # Break word char-by-char with hyphens
                i = 0
                while i < len(word):
                    part = ""
                    while i < len(word) and font.size(part + word[i] + "-")[0] <= max_width:
                        part += word[i]
                        i += 1
                    if i < len(word):
                        lines.append(part + "-")
                    else:
                        current_line = part
    if current_line:
        lines.append(current_line)

    return lines


def load_image_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        image_file = io.BytesIO(response.content)
        return pygame.image.load(image_file).convert_alpha()
    else:
        print("Image couldn't be loaded:", response.status_code)
        return None

def make_circle_image(img_surface, size=(100, 100), border_color=(0, 0, 255), border_width=3):
    img_surface = pygame.transform.smoothscale(img_surface, size)

    mask_surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (size[0]//2, size[1]//2), size[0]//2)

    final_surface = pygame.Surface(size, pygame.SRCALPHA)
    final_surface.blit(img_surface, (0, 0))
    final_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Draw the blue border circle
    pygame.draw.circle(final_surface, border_color, (size[0]//2, size[1]//2), size[0]//2 - border_width//2, border_width)

    return final_surface


def draw_meeting_details(screen, fonts, current_meeting):

    if current_meeting:
        title = current_meeting.get("title", "Başlıksız Toplantı")
        time_str = current_meeting.get("time", "Zaman Yok")
        description = current_meeting.get("description", "")
        participants = current_meeting.get("users", "Belirtilmemiş")

        #Don't change this variables,this is easier for when you are changing the place of the title
        title_y = 30
        line_y = title_y + 42
        time_y = line_y + 5
        description_y = time_y + 25

        # evaluating what would the height of description be so it draws the detail container box based on that
        y = description_y
        wrapped_lines = wrap_text(description, fonts['regular'], screen_width * 0.45)
        for line in wrapped_lines:
            y += 25
        
        # Container Box
        # Keep your existing rectangle position and size
        detail_rect_1 = pygame.Rect(screen_width * 0.35, 30, screen_width * 0.5, 45)
        detail_rect_2 = pygame.Rect(screen_width * 0.35, 20, screen_width * 0.5, 20)
        detail_rect = pygame.Rect(screen_width * 0.35, 20, screen_width * 0.5, y + 50)
        detail_rect_shadow = pygame.Rect(screen_width * 0.35 + 20, 30, screen_width * 0.5, y + 50)

        # Draw shadow behind
        pygame.draw.rect(screen, COLORS["grey"], detail_rect_shadow, border_radius=20)
        pygame.draw.rect(screen, COLORS["grey"], detail_rect_shadow, 2, border_radius=20)

        # Draw gradient rect above shadow
        draw_gradient_rect(screen, COLORS["light"], COLORS["light"], detail_rect, 30)

        # Draw blue rectangle
        draw_gradient_rect(screen, COLORS["primary"], darken_color(COLORS["primary"]), detail_rect_1)

        # Title
        title_font = fonts['bold_large']
        title_surface = title_font.render("Toplantı başlığı: " + title, True, (0, 0, 0))
        title_width = title_surface.get_width()
        box_x = screen_width * 0.35
        box_width = screen_width * 0.5
        title_x = box_x + (box_width - title_width)/2

        screen.blit(title_font.render("Toplantı başlığı: " + title, True, (255, 255, 255)), (title_x, title_y))

        # Time
        screen.blit(fonts['regular'].render("Zaman: " + time_str, True, (0, 0, 0)), (box_x + 10, time_y))

        # Description
        print("📜 Wrapped description lines:", wrapped_lines)
        y = description_y
        wrapped_lines = wrap_text(description, fonts['regular'], screen_width * 0.45)
        screen.blit(fonts['bold'].render("Toplantı Açıklaması:", True, (0, 0, 0)), (box_x + 10, y))
        y += 30
        for line in wrapped_lines:
            screen.blit(fonts['regular'].render(line, True, (0, 0, 0)), (screen_width * 0.38, y))
            y += 25

        participants = current_meeting.get("users", [])

        # Base position
        img_x = screen_width * 0.40 - 30
        initial_x = img_x

        if y >= 300:
            img_y = y + 100 # detaylar kutusu çok uzunsa fotolar daha az aşşaya incekler  
        else:
            img_y = y + 150

        img_spacing = 195  # space between images
        img_num = 0
        i = 0
        rect_x = 0
        rect_y = 0
        radius = 20

        for j,person in enumerate(participants):
            fullName = person.get("fullName", "Anonim").strip()

            # Split by the first space (if any)
            if " " in fullName:
                name_part, surname_part = fullName.split(" ", 1)
            else:
                name_part = fullName
                surname_part = ""

            # Calculate center X for the photo
            center_x = img_x + i * img_spacing + 50  # 50 is half of 100px image width

            # Render name and surname surfaces
            name_surf = fonts['regular'].render(name_part, True, (0, 0, 0))
            surname_surf = fonts['regular'].render(surname_part, True, (0, 0, 0)) if surname_part else None

            # Get widths for centering
            name_w = name_surf.get_width()
            surname_w = surname_surf.get_width() if surname_surf else 0

            # Draw name centered under the image
            screen.blit(name_surf, (center_x - name_w // 2, img_y + 100))

            # Draw surname below name if exists, also centered
            if surname_surf:
                screen.blit(surname_surf, (center_x - surname_w // 2, img_y + 100 + name_surf.get_height()))

            fullName = person.get("fullName", "Anonim")
            picture_path = person.get("picture")

            if picture_path and picture_path.strip() and picture_path != "null":
                full_url = raspberryNodeip + picture_path
                img_surface = load_image_from_url(full_url)
            else:
                img_surface = pygame.image.load("profil.jpg").convert_alpha()

            if img_surface:
                r = 50
                rect_height = 200
                rect_x = center_x - 2 * r + 10
                rect_width = 4 * r - 20
                rect_y = img_y - 35

                img_starting_point = img_y - rect_y
                blue_rect_height = img_starting_point + 100 * (0.6)
                circular_img = make_circle_image(img_surface) # making the image circular
                container_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height) # drawing the container box for the photo in memory
                rect = pygame.Rect(rect_x, rect_y, rect_width, blue_rect_height) # drawing the blue box for the photo in memory
                rect2 = pygame.Rect(rect_x, rect_y + 20, rect_width, blue_rect_height - 20) # drawing the downisde of teh blue box

                draw_gradient_rect(screen, COLORS["primary"], COLORS["primary"], rect, border_radius= radius) # drawing the blue box on the screen
                draw_gradient_rect(screen, COLORS["primary"], darken_color(COLORS["primary"]), rect2) # drawing the down side of the blue box
                pygame.draw.rect(screen,(0,0,0), container_rect, 1, border_radius=radius) # drawing the box on the screen
                screen.blit(circular_img, (img_x + i * img_spacing, img_y)) # drawing the image
                img_num += 1
                i += 1


                if img_num % 5 == 0:
                    img_y += 200
                    img_x = initial_x
                    i = 0




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
    today = datetime.now().date()
    # Determine base Monday for the displayed week
    if today.weekday() >= 5:
        monday = today + timedelta(days=(7 - today.weekday()))
    else:
        monday = today - timedelta(days=today.weekday())

    eng = tr_to_eng.get(tr_day_name, "Monday")
    # Map English weekday to index 0..4 (Mon..Fri)
    weekday_index = ["Monday","Tuesday","Wednesday","Thursday","Friday"].index(eng) if eng in ["Monday","Tuesday","Wednesday","Thursday","Friday"] else 0
    target_date = monday + timedelta(days=weekday_index)
    return target_date.strftime("%Y-%m-%d")


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

# YENİ KOD
# UYGULAMA BAŞLANGICINDA ZAMAN FORMATINI ÇEK
fetch_time_format_config()

fetched_room_name = fetch_room_name()
if fetched_room_name:
    room_name = fetched_room_name

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
    if current_time - last_update_time > 57000:
        
        # Oda adını güncelle
        fetched_room_name = fetch_room_name()
        if fetched_room_name:
            room_name = fetched_room_name

        # Ders Programını update et
        update_data() # This should update `ders_programi`

    # Clear screen with gradient background
    draw_gradient_background(screen, darken_color(COLORS["Charcoal"]), COLORS["white"])

    print(f"Display mode: {display_mode}, Time since last switch: {pygame.time.get_ticks() - last_switch_time}")
    
    # Update scroll indices every 10 seconds
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
    
    now = pygame.time.get_ticks() # This is 'current_time'

    # Flag to break outer loop once a current meeting is found
    found_current_meeting_this_cycle = False

    #if there is a current meeting switch to the meeting details every 30 seconds
    if display_mode == "grid" and now - last_switch_time > 30000:
        # Clear meetings *before* repopulating it only when entering this block
        meetings.clear() # Or meetings = [] if you prefer a new list instance
        
        for day, hours in ders_programi.items():
            for hour, entry in hours.items():
                if entry["durum"] == "Dolu" and entry.get("rendezvous_id"):
                    rendezvous_id = entry["rendezvous_id"]

                    if not check_if_slot_is_current(day,hour,time_suffix):
                        continue

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

                        # Second, if 'data' itself is a list, treat it as the main data
                        elif isinstance(data, list) and len(data) > 0:
                            details = data[0]
                            # In this case, there's no `groupResult` key, so group_members remains an empty list by default.
                        
                        # Now, with 'details' potentially populated from either format, proceed
                        if details: # Only proceed if details were successfully extracted from either format
                            users = []
                            # Add organizer as the first user
                            users = [{"fullName": details.get("fullName", entry["düzenleyen"]), "picture": details.get("picture")}]

                            # If it's a group, append group members
                            if details.get("isGroup") in [0, 1] and group_members:
                                users += [{"fullName": member["fullName"], "picture": member.get("picture")} for member in group_members]



                            meeting_info = {
                                "rendezvous_id": rendezvous_id,
                                "day": get_date_from_day_name(day),
                                "time": f"{hour}-{int(hour.split(':')[0])+1:02d}{time_suffix}",
                                "title": details.get("title", entry["aktivite"]),
                                "organizer": details.get("fullName", entry["düzenleyen"]),
                                "users": users,
                                "description": details.get("message", ""),
                                "room_name": {room_name},
                                "img": details.get("picture", "image here")
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

    # switch back to the schedule after 10 seconds 
    elif display_mode == "detail" and now - last_switch_time > 10000:
            print(f"[{now}] Meeting ended or detail timeout. Switching back to grid.")
            display_mode = "grid"
            current_meeting = None # Clear current meeting data

    # Main Drawing Logic
    if display_mode == "grid":
        # Pass required arguments to `draw_schedule_table`
        draw_schedule_table(screen, fonts) 
    else: # display_mode == "detail"        
        draw_gradient_background(screen,darken_color(COLORS["Charcoal"]), COLORS["white"]) 
        
        draw_meeting_details_v2(screen, fonts, current_meeting)

    draw_footer(screen, fonts) # Only call once at the end

    pygame.display.flip()

pygame.quit()
