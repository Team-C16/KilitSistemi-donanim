#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import font
import requests
import qrcode
from PIL import Image, ImageTk
import io
import jwt
import time
import json
from datetime import datetime, timedelta
import threading
import queue
import sys

# ----------------------------------------------------------------------
# 1. SABİTLER VE API AYARLARI
# ----------------------------------------------------------------------

jwt_secret = os.getenv("jwt_secret")
nodeip = os.getenv("nodeip")
room_id = os.getenv("room_id")
ACCESS_TYPE = 1
last_switch_time = datetime.now()

# ----------------------------------------------------------------------
# 2. API BAĞLANTI HATASI İÇİN SAHTE (FALLBACK) VERİLER
# ----------------------------------------------------------------------
# (Not: API hatasında eski veriyi koru mantığı eklendiği için
# bu veriler artık sadece ilk açılışta veya ciddi bir
# 'transform_schedule' hatasında kullanılır.)

FALLBACK_DATA = {
    "schedule": [
        {
            "title": "BIM 229 - G1 (YM)", 
            "hour": "14:00", 
            "day": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), 
            "fullName": "Hakan Gençoğlu", 
            "rendezvous_id": "3"
        },
        {
            "title": "BIM 229 - G1 (BM)", 
            "hour": "15:00", 
            "day": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), 
            "fullName": "Hakan Gençoğlu", 
            "rendezvous_id": "6"
        }
    ]
}

FALLBACK_DETAILS_DATA = {
    "3": {
        "dataResult": [{"title": "BIM 229 - G1 (YM)", "message": "API hatası, sahte veri gösteriliyor.", "hour": "14:00", "fullName": "Hakan Gençoğlu", "isGroup": 1}],
        "groupResult": [{"fullName": "Kerem Yavuz"}]
    },
    "6": {
        "dataResult": [{"title": "BIM 229 - G1 (BM)", "message": "API hatası, sahte veri gösteriliyor.", "hour": "15:00", "fullName": "Hakan Gençoğlu", "isGroup": 1}],
        "groupResult": [{"fullName": "Hasan Ari"}]
    }
}

# ----------------------------------------------------------------------
# 3. VERİ İŞLEME YARDIMCI FONKSİYONLARI
# ----------------------------------------------------------------------

def transform_schedule(api_data, date_keys_to_show): # <-- DİKKAT: Parametre eklendi
    """
    API'den gelen veriyi, YALNIZCA 'date_keys_to_show' listesindeki
    tarihlere göre 'ders_programi' sözlüğüne dönüştürür.
    Bu, "geçen haftanın Pazartesisi" hatasını düzeltir.
    """
    hours = [f"{h:02}:00" for h in range(9, 19)]

    # 1. Adım: Programı YALNIZCA gösterilecek 5 tarih için "Boş" olarak doldur
    ders_programi = {}
    for date_key in date_keys_to_show: # <-- Artık tarih anahtarlarını kullanıyor
        ders_programi[date_key] = {}
        for hour in hours:
            ders_programi[date_key][hour] = {
                "durum": "Boş", "aktivite": "", "düzenleyen": "", "rendezvous_id": ""
            }

    # 2. Adım: API verisiyle "Dolu" olanları üzerine yaz
    schedule = api_data.get("schedule", [])
    for entry in schedule:
        try:
            utc_time = datetime.strptime(entry["day"], "%Y-%m-%dT%H:%M:%S.%fZ")
            local_time = utc_time + timedelta(days=1) # Orijinal +1 gün mantığı
            
            api_date_key = local_time.strftime("%Y-%m-%d") # <-- API'den gelen verinin tarih anahtarı
            time_str = entry["hour"].split(":")[0]
            hour_str = f"{int(time_str):02d}:00"

            # --- BU KONTROL HATAYI DÜZELTİYOR ---
            # API'den gelen bu tarih, bizim göstermek istediğimiz 5 günden biri mi?
            if api_date_key in ders_programi and hour_str in ders_programi[api_date_key]:
                ders_programi[api_date_key][hour_str] = {
                    "durum": "Dolu",
                    "aktivite": entry["title"],
                    "düzenleyen": entry["fullName"],
                    "rendezvous_id": entry["rendezvous_id"],
                }
        except Exception as e:
            print(f"⚠️ Zamanlama verisi işlenirken hata: {e}, Girdi: {entry}")
    return ders_programi

def check_if_slot_is_current(day_name, hour_str):
    """
    Verilen gün adı ve saatin şu an olup olmadığını kontrol eder.
    """
    try:
        now = datetime.now()
        today_name = now.strftime('%A')
        gun_map = {
            "Pazartesi": "Monday", "Salı": "Tuesday", "Çarşamba": "Wednesday",
            "Perşembe": "Thursday", "Cuma": "Friday", "Cumartesi": "Saturday", "Pazar": "Sunday"
        }
        english_day_name = gun_map.get(day_name, day_name)
        
        if english_day_name != today_name:
            return False
        
        start_hour = int(hour_str.split(':')[0])
        start_minute = int(hour_str.split(':')[1])
        start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_time = now.replace(hour=start_hour + 1, minute=start_minute, second=0, microsecond=0)
        
        return True # start_time <= now < end_time
    except Exception as e:
        print(f"Zaman kontrol hatası: {e}")
        return False

def create_shadowed_frame(parent, bg="white", shadow_color="#AAAAAA", shadow_x=5, shadow_y=5, bd=1, relief="solid"):
    """
    İçine widget yerleştirilebilen, sahte gölgeli bir çerçeve oluşturur.
    """
    # 1. Dış Çerçeve (Gölge)
    shadow_frame = tk.Frame(parent, bg=shadow_color)
    
    # 2. İç Çerçeve (Asıl İçerik)
    content_frame = tk.Frame(shadow_frame, bg=bg, relief=relief, bd=bd)
    
    # 3. İçeriği, gölgeyi gösterecek şekilde 'pack' ile yerleştir
    content_frame.pack(expand=True, fill="both", 
                       padx=(0, shadow_x), 
                       pady=(0, shadow_y))
    
    # 4. İçerik çerçevesini ana çerçevenin bir özelliği olarak ata
    shadow_frame.content_frame = content_frame
    
    # 5. Ekrana yerleştirilmesi gereken ana konteyneri (gölgeyi) döndür
    return shadow_frame

# ----------------------------------------------------------------------
# 4. ANA TKINTER UYGULAMA SINIFI
# ----------------------------------------------------------------------

class RoomScheduleApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Oda Rezervasyon Sistemi")

        # --- MANUEL TAM EKRAN AYARI ('xinit' için) ---
        self.app_width = self.winfo_screenwidth()
        self.app_height = self.winfo_screenheight()
        self.geometry(f"{self.app_width}x{self.app_height}+0+0")
        self.overrideredirect(True) # Pencere kenarlıklarını kaldır
        self.config(cursor="none")  # Fare imlecini gizle
        self.bind("<Escape>", lambda e: self.quit_app())
        
        print(f"Ekran Boyutu: {self.app_width}x{self.app_height}")

        # --- RENK VE FONT AYARLARI ---
        self.colors = {
            "background": "#F0F0F0", # Arka plan (açık gri)
            "primary": "#33648A",    # Koyu Mavi (Lapis-Lazuli)
            "available": "#86BBD8",  # Açık Mavi (Carolina-blue)
            "unavailable": "#8E4162",# Kırmızı/Magenta
            "highlight": "#F1C40F",  # Sarı (Mevcut Saat)
            "light": "#FFFFFF",      # Beyaz (Kartlar)
            "dark": "#2C3E50",       # Koyu Gri (Yazı)
            "text_primary": "#000000",
            "white": "#FFFFFF",
        }

        self.fonts = {
            "title": font.Font(family="Arial", size=int(self.app_height * 0.030), weight="bold"),
            "subtitle": font.Font(family="Arial", size=int(self.app_height * 0.020), weight="bold"),
            "day": font.Font(family="Arial", size=int(self.app_height * 0.022), weight="bold"),
            "hour": font.Font(family="Arial", size=int(self.app_height * 0.021)),
            "cell_main": font.Font(family="Arial", size=int(self.app_height * 0.020), weight="bold"),
            "cell_sub": font.Font(family="Arial", size=int(self.app_height * 0.018)),
            "info": font.Font(family="Arial", size=int(self.app_height * 0.016)),
            "footer": font.Font(family="Arial", size=int(self.app_height * 0.025)),
        }
        
        # --- TARİH YÖNETİMİ ---
        self.dict_tr = {
            "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
            "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"
        }
        start_date = datetime.now()
        self.days_to_display = [(start_date + timedelta(days=i)) for i in range(5)]
        self.days_tr_turkish = [self.dict_tr[d.strftime("%A")] for d in self.days_to_display]
        self.date_keys = [d.strftime("%Y-%m-%d") for d in self.days_to_display]
        
        # --- GUI DURUM DEĞİŞKENLERİ ---
        self.room_name = "Oda Yükleniyor..."
        self.ders_programi = {}
        self.display_mode = "grid"
        self.current_meeting_data = None
        self.qr_image = None
        self.participant_images = [] # Resim referanslarını saklamak için
        self.api_queue = queue.Queue() # Thread-safe GUI güncelleme sırası

        # --- ANA ARAYÜZ DÜZENİ (LAYOUT) ---
        self.configure(bg=self.colors["background"])
        self.grid_rowconfigure(0, weight=1) # Ana içerik
        self.grid_rowconfigure(1, weight=0, minsize=int(self.app_height * 0.07)) # Footer
        self.grid_columnconfigure(0, weight=1)
        
        self.main_frame = tk.Frame(self, bg=self.colors["background"])
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=3, minsize=int(self.app_width*0.28)) # Sol: QR
        self.main_frame.grid_columnconfigure(1, weight=7) # Sağ: Takvim
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self.footer_frame = tk.Frame(self, bg=self.colors["primary"])
        self.footer_frame.grid(row=1, column=0, sticky="sew")
        self.build_footer()
        
        self.qr_card_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        self.qr_card_frame.grid(row=0, column=0, sticky="nsew")
        self.build_qr_card()
        
        self.content_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Takvim Görünümü
        shadow_schedule_frame = create_shadowed_frame(
            parent=self.content_frame, bg=self.colors["light"], 
            shadow_color="#AAAAAA", shadow_x=5, shadow_y=5, bd=1
        )
        shadow_schedule_frame.grid(row=0, column=0, sticky="nsew")
        self.schedule_view_frame = shadow_schedule_frame.content_frame
        
        self.schedule_cells = {}
        self.day_header_labels = {}
        self.hour_labels = {}
        self.build_schedule_view()
        
        # Detay Görünümü (Başlangıçta gizli)
        self.detail_view_frame = tk.Frame(self.content_frame, bg=self.colors["background"])
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.build_detail_view()
        self.detail_view_frame.grid_remove()

        # --- PERİYODİK GÖREVLERİ BAŞLAT ---
        self.after(100, self.start_periodic_updates) # 100ms sonra başlat
        self.after(100, self.process_api_queue)

    def start_periodic_updates(self):
        """Tüm periyodik görevleri başlatan ana fonksiyon."""
        self.update_footer_clock()       # Bağımsız saat döngüsü (Her saniye)
        self.master_update_loop()        # Ana döngümüz (Her 30 saniye)

    def master_update_loop(self):
        """
        Ana güncelleme döngüsü. Her 30 saniyede bir tüm API verilerini
        (QR, Oda Adı, Takvim) çekmek için thread'leri başlatır.
        """
        print(f"[{datetime.now()}] Ana güncelleme döngüsü başladı...")
        
        self.run_in_thread(self.fetch_qr_token)
        self.run_in_thread(self.fetch_room_name)
        self.run_in_thread(self.update_data)
        
        self.after(30000, self.master_update_loop)

    def run_in_thread(self, target_func, *args):
        """Verilen fonksiyonu GUI'yi dondurmamak için bir thread'de çalıştırır."""
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def process_api_queue(self):
        """
        API thread'lerinden gelen sonuçları işler ve GUI'yi günceller.
        """
        try:
            while not self.api_queue.empty():
                task_name, data = self.api_queue.get_nowait()
                
                if task_name == "qr_token":
                    self.update_qr_image(data)
                
                elif task_name == "room_name":
                    self.room_name = data or "Oda Yok"
                    self.qr_room_name_label.config(text=f"➡️ {self.room_name}")

                elif task_name == "schedule_data":
                    self.ders_programi = data
                    self.update_schedule_widgets()
                    
                    # Veri güncellendi, ŞİMDİ toplantı var mı diye kontrol et.
                    print("Takvim verisi işlendi, mevcut toplantı kontrol ediliyor...")
                    self.check_for_current_meeting() 
                
                elif task_name == "detail_data":
                    print("DETAIL RECEIVED:", data)
                    self.current_meeting_data = data
                    self.update_detail_widgets(details=True)

                    
        except queue.Empty:
            pass # Sıra boş, sorun yok
        finally:
            self.after(100, self.process_api_queue) # 100ms'de bir sırayı kontrol et

    # ------------------------------------------------------------------
    # 4.1. API ÇAĞRI FONKSİYONLARI (Thread'lerde çalışır)
    # ------------------------------------------------------------------
    
    def fetch_room_name(self):
        """Oda adını çeker ve kuyruğa atar."""
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, jwt_secret, algorithm="HS256")
            url = f"{nodeip}/getQRCodeToken"
            headers = {"Content-Type": "application/json"}
            data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "room_name": 1, "accessType": "{ACCESS_TYPE}"}}'
            response = requests.post(url, headers=headers, data=data, timeout=5)
            
            if response.status_code == 200:
                name = response.json().get("room_name")
                self.api_queue.put(("room_name", name))
            else:
                print(f"Oda Adı hatası: {response.status_code}")
                pass # Hata durumunda eski veriyi koru
        except Exception as e:
            print(f"API (Oda Adı) bağlantı hatası: {e}")
            pass # Bağlantı hatasında da eski veriyi koru

    def fetch_qr_token(self):
        """QR token'ı çeker ve kuyruğa atar."""
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, jwt_secret, algorithm="HS256")
            url = f"{nodeip}/getQRCodeToken"
            headers = {"Content-Type": "application/json"}
            data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "accessType": "{ACCESS_TYPE}"}}'
            response = requests.post(url, headers=headers, data=data, timeout=5)
            token = response.json().get("token") if response.status_code == 200 else None
            self.api_queue.put(("qr_token", token))
        except Exception as e:
            print(f"API (QR Token) bağlantı hatası: {e}")
            pass # Hata durumunda eski veriyi koru

    def update_data(self):
        """Takvim verisini çeker ve kuyruğa atar."""
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, jwt_secret, algorithm="HS256")
            payload = {"room_id": room_id, "token": encoded_jwt}
            response = requests.post(f"{nodeip}/getSchedule", json=payload, timeout=5)
            response.raise_for_status()
            api_response = response.json()
            new_data = api_response[0] if isinstance(api_response, list) and api_response else api_response
            
            # transform_schedule'a self.date_keys'i yolla
            ders_programi = transform_schedule(new_data, self.date_keys) 
            self.api_queue.put(("schedule_data", ders_programi))
            
        except Exception as e:
            print(f"⚠️ API (Takvim) bağlantı hatası, eski veri korunuyor. Hata: {e}")
            pass # Hata durumunda eski veriyi koru
            
    def fetch_details_data(self, rendezvous_id):
        """Toplantı detay verisini çeker ve kuyruğa atar."""
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, jwt_secret, algorithm="HS256")
            url = f"{nodeip}/getScheduleDetails"
            headers = {"Content-Type": "application/json"}
            payload = {"room_id": room_id, "token": encoded_jwt, "rendezvous_id": rendezvous_id}
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
            response.raise_for_status()
            self.api_queue.put(("detail_data", response.json()))
        except Exception as e:
            print(f"⚠️ API (Detay) hatası: {e}")
            pass # Hata durumunda (muhtemelen) eski detayda kalır

    def load_image_from_url_pil(self, url, size=(100, 100)):
        """Bir URL'den resim yükler ve PhotoImage'e dönüştürür."""
        try:
            full_url = f"{nodeip}{url}"
            response = requests.get(full_url, timeout=3)
            response.raise_for_status()
            img_data = io.BytesIO(response.content)
            img = Image.open(img_data).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return self.default_profile_image(size)

    def default_profile_image(self, size=(100, 100)):
        """Varsayılan bir profil resmi oluşturur."""
        img = Image.new('RGB', size, color=self.colors["primary"])
        return ImageTk.PhotoImage(img)

    # ------------------------------------------------------------------
    # 4.2. GUI İNŞA FONKSİYONLARI (Widget oluşturma)
    # ------------------------------------------------------------------

    def build_qr_card(self):
        """Sol taraftaki QR Kod Kartını oluşturan widget'lar."""
        shadow_card = create_shadowed_frame(
            parent=self.qr_card_frame, bg=self.colors["light"], 
            shadow_color="#AAAAAA", shadow_x=5, shadow_y=5, bd=1
        )
        shadow_card.pack(expand=True, fill="both")
        content_frame = shadow_card.content_frame

        header_frame = tk.Frame(content_frame, bg=self.colors["primary"])
        header_frame.pack(side="top", fill="x")
        tk.Label(header_frame, text="Odaya Erişim", font=self.fonts["subtitle"], bg=self.colors["primary"], fg=self.colors["white"]).pack(pady=10)
        
        self.qr_label = tk.Label(content_frame, bg=self.colors["light"])
        self.qr_label.pack(pady=10, padx=10)
        
        tk.Label(content_frame, text="QR Kodu Uygulamadan Taratın", font=self.fonts["info"], bg=self.colors["light"], fg=self.colors["text_primary"]).pack(pady=5)
        
        self.qr_room_name_label = tk.Label(content_frame, text=f"➡️ {self.room_name}", font=self.fonts["title"], bg=self.colors["light"], fg=self.colors["text_primary"])
        self.qr_room_name_label.pack(pady=(5, 20))

    def build_footer(self):
        """Alt taraftaki Footer barını oluşturur."""
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_rowconfigure(0, weight=1) 
        
        dikey_padding = int(self.app_height * 0.015) # Yüksekliği artırdık

        info_label = tk.Label(self.footer_frame, text="pve.izu.edu.tr/randevu ← Randevu İçin", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        info_label.grid(row=0, column=0, sticky="w", padx=20, pady=dikey_padding)

        self.clock_label = tk.Label(self.footer_frame, text="⏰ Yükleniyor...", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        self.clock_label.grid(row=0, column=1, sticky="e", padx=20, pady=dikey_padding)

    def build_schedule_view(self):
        """
        Sağ taraftaki Takvim Tablosunu oluşturur.
        (Gün/Tarih/Bugün etiketleri birleştirilmiş versiyon)
        """
        self.hours = [f"{h:02}:00" for h in range(9, 19)]
        grid_frame = self.schedule_view_frame
        
        saat_sutunu_genisligi = int(self.app_width * 0.05)
        icerik_cercevesi_genisligi = (self.app_width * 0.72) - saat_sutunu_genisligi 
        hucre_genisligi = int(icerik_cercevesi_genisligi / 5) - 9 # 5 gün
        self.wrap_limit = int(hucre_genisligi * 0.9)
        
        toplam_icerik_yuksekligi = int(self.app_height * 0.92) 
        baslik_yuksekligi = int(toplam_icerik_yuksekligi * 0.10)
        kalan_yukseklik = toplam_icerik_yuksekligi - baslik_yuksekligi
        hucre_yuksekligi = int(kalan_yukseklik / len(self.hours))
        
        grid_frame.grid_rowconfigure(0, weight=0, minsize=baslik_yuksekligi) # Gün Başlıkları
        for i in range(len(self.hours)):
            grid_frame.grid_rowconfigure(i + 1, weight=0, minsize=hucre_yuksekligi) # İçerik
            
        grid_frame.grid_columnconfigure(0, weight=0, minsize=saat_sutunu_genisligi) # Saat
        for i in range(len(self.days_tr_turkish)):
            grid_frame.grid_columnconfigure(i + 1, weight=0, minsize=hucre_genisligi) # Günler
            
        tk.Label(grid_frame, text="Saat", font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"], relief="solid", bd=1).grid(
            row=0, column=0, sticky="nsew"
        )
        
        for i, day_tr in enumerate(self.days_tr_turkish):
            date_str = self.days_to_display[i].strftime("%d.%m")
            
            header_cell_frame = tk.Frame(grid_frame, bg=self.colors["primary"], relief="solid", bd=1)
            header_cell_frame.grid(row=0, column=i+1, sticky="nsew")
            header_cell_frame.pack_propagate(False) 

            day_name_label = tk.Label(header_cell_frame, text=day_tr, font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"])
            day_name_label.pack(side="top", pady=(5,0))
            
            date_label = tk.Label(header_cell_frame, text=date_str, font=self.fonts["info"], bg=self.colors["primary"], fg=self.colors["white"])
            date_label.pack(side="top")
            
            today_label = tk.Label(header_cell_frame, text="Bugün", font=self.fonts["info"], bg=self.colors["primary"], fg=self.colors["white"])
            
            self.day_header_labels[day_tr] = {
                "frame": header_cell_frame,
                "day_name": day_name_label,
                "date": date_label,
                "today": today_label
            }

        for j, hour in enumerate(self.hours):
            hour_label = tk.Label(grid_frame, text=hour, font=self.fonts["hour"], bg=self.colors["light"], fg=self.colors["text_primary"], relief="solid", bd=1)
            hour_label.grid(row=j+1, column=0, sticky="nsew")
            self.hour_labels[hour] = hour_label
            
            for i, day in enumerate(self.days_tr_turkish):
                cell_frame_container = tk.Frame(grid_frame, relief="solid", bd=1)
                cell_frame_container.grid(row=j+1, column=i+1, sticky="nsew")
                cell_frame_container.grid_propagate(False) 
                
                cell_frame = tk.Frame(cell_frame_container, bg=self.colors["available"])
                cell_frame.pack(expand=True, fill="both")

                label1 = tk.Label(cell_frame, text="", font=self.fonts["cell_main"], bg=self.colors["available"], fg=self.colors["white"],
                                  wraplength=self.wrap_limit, justify="center")
                label1.place(relx=0.5, rely=0.35, anchor="center")
                
                label2 = tk.Label(cell_frame, text="", font=self.fonts["cell_sub"], bg=self.colors["available"], fg=self.colors["white"],
                                  wraplength=self.wrap_limit, justify="center")
                label2.place(relx=0.5, rely=0.65, anchor="center")
                
                self.schedule_cells[day] = self.schedule_cells.get(day, {})
                self.schedule_cells[day][hour] = {"container": cell_frame_container, "frame": cell_frame, "label1": label1, "label2": label2}
                
    def build_detail_view(self):
        """Toplantı Detay görünümünü oluşturur (görseldeki gibi değil, tahmini)."""
        frame = self.detail_view_frame
        frame.grid_columnconfigure(0, weight=1)
        
        detail_box = tk.Frame(frame, bg=self.colors["light"], relief="solid", bd=2)
        detail_box.grid(row=0, column=0, sticky="new", pady=(self.app_height*0.05))
        detail_box.grid_columnconfigure(0, weight=1)
        
        self.detail_title = tk.Label(detail_box, text="Toplantı Başlığı", font=self.fonts["title"], bg=self.colors["primary"], fg=self.colors["white"])
        self.detail_title.grid(row=0, column=0, sticky="ew", ipady=10)
        
        self.detail_time = tk.Label(detail_box, text="Zaman: 00:00", font=self.fonts["cell_main"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="w")
        self.detail_time.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        self.detail_desc = tk.Label(detail_box, text="Açıklama...", font=self.fonts["cell_sub"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="nw", justify="left", 
                                    wraplength=self.app_width*0.6)
        self.detail_desc.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        
        self.participants_frame = tk.Frame(frame, bg=self.colors["background"])
        self.participants_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        tk.Label(self.participants_frame, text="Katılımcılar", font=self.fonts["subtitle"], bg=self.colors["background"]).pack()

    # ------------------------------------------------------------------
    # 4.3. GUI GÜNCELLEME FONKSİYONLARI (Queue'dan tetiklenir)
    # ------------------------------------------------------------------

    def update_qr_image(self, qr_data):
        """QR kod etiketini yeni veriyle günceller."""
        if not qr_data: qr_data = "API_ERROR"
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            qr_size = int(self.app_width * 0.20)
            img = img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image)
        except Exception as e:
            print(f"QR oluşturma hatası: {e}")

    def update_footer_clock(self):
        """Saati her saniye günceller."""
        now = datetime.now()
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")
        self.clock_label.config(text=f"⏰ {date_str}  •  {time_str}")
        self.after(1000, self.update_footer_clock)

        # bir meeting için kontrol eder
        self.check_for_current_meeting()

    def update_schedule_widgets(self):
        """'self.ders_programi' verisine bakarak takvim widget'larını günceller."""
        if not self.ders_programi: return
            
        today_tr = self.days_tr_turkish[0]
        current_hour_str = f"{datetime.now().hour:02d}:00"
        
        # Gün Başlıklarını Güncelle
        for day in self.days_tr_turkish:
            if day not in self.day_header_labels: continue
            widgets = self.day_header_labels[day]
            
            if day == today_tr:
                widgets["frame"].config(bg=self.colors["available"])
                widgets["day_name"].config(bg=self.colors["available"], fg=self.colors["dark"])
                widgets["date"].config(bg=self.colors["available"], fg=self.colors["dark"])
                widgets["today"].config(bg=self.colors["available"], fg=self.colors["dark"])
                widgets["today"].pack(side="top", fill="x", pady=(0,5))
            else:
                widgets["frame"].config(bg=self.colors["primary"])
                widgets["day_name"].config(bg=self.colors["primary"], fg=self.colors["white"])
                widgets["date"].config(bg=self.colors["primary"], fg=self.colors["white"])
                widgets["today"].config(bg=self.colors["primary"], fg=self.colors["white"])
                widgets["today"].pack_forget()

        # Saat Etiketlerini Güncelle
        for hour, label in self.hour_labels.items():
            if hour == current_hour_str and today_tr in self.ders_programi:
                label.config(bg=self.colors["highlight"], fg=self.colors["dark"])
            else:
                label.config(bg=self.colors["light"], fg=self.colors["text_primary"])

        # Hücre İçeriklerini Güncelle (Tarih Anahtarı ile)
        for i, day_tr in enumerate(self.days_tr_turkish):
            date_key = self.date_keys[i] # "2025-11-15"
            
            if date_key not in self.ders_programi: continue
            
            for hour in self.hours:
                if hour not in self.ders_programi[date_key]: continue
                
                cell = self.schedule_cells[day_tr][hour]
                data = self.ders_programi[date_key][hour] 
                status = data["durum"]
                
                if status == "Boş":
                    bg = self.colors["available"]; fg = self.colors["white"]
                    label1_text = "⚪️ Randevuya"; label2_text = "Uygun"
                else:
                    bg = self.colors["unavailable"]; fg = self.colors["white"]
                    label1_text = data.get("aktivite", "Dolu")
                    label2_text = f"👤 {data.get('düzenleyen', '')}"

                cell["frame"].config(bg=bg)
                cell["label1"].config(text=label1_text, bg=bg, fg=fg)
                cell["label2"].config(text=label2_text, bg=bg, fg=fg)
                
                if hour == current_hour_str and day_tr == today_tr:
                    cell["container"].config(highlightbackground=self.colors["highlight"], highlightthickness=3, bd=0)
                else:
                    cell["container"].config(highlightthickness=0, bd=1)

    def update_detail_widgets(self, details = False):
        if not self.current_meeting_data: 
            return
        # Your API returns a list, not a dict with "dataResult"
        main_data = self.current_meeting_data[0]

        self.detail_title.config(text=main_data.get("title", "Başlıksız"))
        self.detail_time.config(text=f"Zaman: {main_data.get('hour', '00:00')}")
        self.detail_desc.config(text=main_data.get("message", "Açıklama yok."))

        # Temizle
        for widget in self.participants_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        self.participant_images.clear()

        # Your API has NO groupResult, only ONE person
        participants = [main_data]

        participants_grid = tk.Frame(self.participants_frame, bg=self.colors["background"])
        participants_grid.pack(fill="x", expand=True, pady=10)

        for i, person in enumerate(participants):
            if not person or not person.get("fullName"):
                continue

            participants_grid.grid_columnconfigure(i, weight=1)

            person_frame = tk.Frame(participants_grid, bg=self.colors["light"], relief="solid", bd=1)
            person_frame.grid(row=0, column=i, padx=10, sticky="n")

            img_url = person.get("picture")
            img = (self.load_image_from_url_pil(img_url) if img_url 
                else self.default_profile_image())

            self.participant_images.append(img)

            tk.Label(person_frame, image=img, bg=self.colors["primary"]).pack(pady=(10,0))
            tk.Label(
                person_frame, 
                text=person.get("fullName"), 
                font=self.fonts["info"], 
                bg=self.colors["light"], 
                wraplength=120
            ).pack(pady=10, padx=5)


    # ------------------------------------------------------------------
    # 4.4. GÖRÜNÜM DEĞİŞTİRME VE KONTROL
    # ------------------------------------------------------------------
    
    def check_for_current_meeting(self):
        """
        Mevcut bir toplantı olup olmadığını kontrol eder ve görünümü değiştirir.
        'process_api_queue' tarafından tetiklenir.
        """
        global last_switch_time
        print((datetime.now() - last_switch_time).total_seconds().__floor__())
        if not self.ders_programi:
            return

        found_meeting = False
        today_tr = self.days_tr_turkish[0]   # "Cumartesi"
        today_date_key = self.date_keys[0]   # "2025-11-15"
        
        if today_date_key in self.ders_programi:
            for hour, entry in self.ders_programi[today_date_key].items():
                
                if entry["durum"] == "Dolu" and check_if_slot_is_current(today_tr, hour):
                    
                    found_meeting = True
                    rendezvous_id = entry["rendezvous_id"]
                    
                    current_id = None

                    # this is considering the two posibilities of self.current_meeting_data being a dictionary or a list
                    if isinstance(self.current_meeting_data, dict):
                        data_list = self.current_meeting_data.get("dataResult", [])
                        if isinstance(data_list, list) and len(data_list) > 0:
                            current_id = data_list[0].get("rendezvous_id")

                    elif isinstance(self.current_meeting_data, list) and len(self.current_meeting_data) > 0:
                        current_id = self.current_meeting_data[0].get("rendezvous_id")

                    if (self.display_mode == "detail" and (datetime.now() - last_switch_time).total_seconds() >= 10):
                        print("I'm here!!!!!!!")
                        self.show_schedule_view()
                        last_switch_time = datetime.now()

                    if (self.display_mode == "grid" or str(current_id) != str(rendezvous_id)) and (datetime.now() - last_switch_time).total_seconds() >= 30:
                        print(f"Yeni toplantı bulundu: {rendezvous_id}. Detaylar getiriliyor...") 
                        self.show_detail_view(rendezvous_id)
                        last_switch_time = datetime.now()
                    break
                
        if not found_meeting and self.display_mode == "detail":
            print("Toplantı bitti, takvime dönülüyor.")
            self.show_schedule_view()

    def show_schedule_view(self):
        """Sadece Takvim görünümüne geçer."""
        self.detail_view_frame.grid_remove()
        self.schedule_view_frame.grid(row=0, column=0, sticky="nsew")
        self.display_mode = "grid"
        self.current_meeting_data = None

    def show_detail_view(self, rendezvous_id):
        """Sadece Detay görünümüne geçer ve veriyi ister."""
        self.schedule_view_frame.grid_remove()
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.display_mode = "detail"
        self.run_in_thread(self.fetch_details_data, rendezvous_id)

    def quit_app(self):
        """Uygulamayı güvenle kapatır."""
        print("Çıkış yapılıyor...")
        self.destroy()

# ----------------------------------------------------------------------
# 5. UYGULAMAYI BAŞLAT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    
    # Gerekli importları en başa taşı
    import tkinter as tk
    from tkinter import font
    import requests
    import qrcode
    from PIL import Image, ImageTk, ImageOps
    import io
    import jwt
    import time
    import json
    from datetime import datetime, timedelta
    import threading
    import queue
    import sys
    
    try:
        app = RoomScheduleApp()
        app.mainloop()
    except tk.TclError as e:
        print(f"Kritik TclError: {e}", file=sys.stderr)
        print("Masaüstü ortamı (Xorg) bulunamadı. 'xinit' veya 'startx' ile çalıştırın.", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Eksik kütüphane: {e}", file=sys.stderr)
        print("Lütfen 'sudo apt-get install python3-tk python3-pil python3-pil.imagetk'", file=sys.stderr)
        print("Ve 'pip install requests qrcode pillow pyjwt' komutlarını çalıştırın.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Uygulama başlatılırken kritik bir hata oluştu: {e}", file=sys.stderr)
        sys.exit(1)
