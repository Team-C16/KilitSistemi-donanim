#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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

JWT_SECRET = os.getenv("jwt_secret")
RASPBERRY_NODE_IP = os.getenv("nodeip")
room_id = os.getenv("room_id")
ACCESS_TYPE = 1
last_switch_time = datetime.now()

# ----------------------------------------------------------------------
# 2. DATA DÖNÜŞÜM VE KONTROL FONKSİYONLARI
# ----------------------------------------------------------------------

def transform_schedule(api_data, date_keys_to_show, time_suffix, start_hour,end_hour): 
    """
    API'den gelen veriyi işler.
    GÜNCELLEME: time_suffix parametresi eklendi.
    Anahtarlar artık örn: "14:00" yerine "14:30" formatında olabilir.
    """
    # Dinamik saat listesi (örn: 09:30, 10:30...)
    hours = [f"{h:02}{time_suffix}" for h in range(start_hour,end_hour)]

    # 1. Adım: Programı boş olarak başlat
    ders_programi = {}
    for date_key in date_keys_to_show:
        ders_programi[date_key] = {}
        for hour in hours:
            ders_programi[date_key][hour] = {
                "durum": "Boş", "aktivite": "", "düzenleyen": "", "rendezvous_id": ""
            }

    # 2. Adım: API verisiyle doldur
    schedule = api_data.get("schedule", [])
    for entry in schedule:
        try:
            # Tarih parse etme
            day_str = entry.get("day", "")
            # (Varsa .000Z gibi kısımları temizle)
            if "." in day_str:
                day_str = day_str.split(".")[0]
            
            utc_time = datetime.strptime(day_str, "%Y-%m-%dT%H:%M:%S")
            # +1 Gün mantığı (Orijinal kodunuzdaki mantık korundu)
            local_time = utc_time + timedelta(days=1)
            
            api_date_key = local_time.strftime("%Y-%m-%d")

            # Saat parse etme ve suffix uygulama
            # API "14:00" veya "14:30" gönderebilir, biz sadece saat kısmını alıp kendi suffix'imizi ekliyoruz.
            raw_hour = entry.get("hour", "00:00")
            hour_part = raw_hour.split(":")[0]
            
            # Anahtar oluşturma: "14" + ":30" -> "14:30"
            hour_str = f"{int(hour_part):02d}{time_suffix}"

            if api_date_key in ders_programi and hour_str in ders_programi[api_date_key]:
                ders_programi[api_date_key][hour_str] = {
                    "durum": "Dolu",
                    "aktivite": entry.get("title", ""),
                    "düzenleyen": entry.get("fullName", ""),
                    "rendezvous_id": entry.get("rendezvous_id", ""),
                }
        except Exception as e:
            print(f"⚠️ Zamanlama verisi işlenirken hata: {e}, Girdi: {entry}")
    
    return ders_programi

def check_if_slot_is_current(day_name, hour_str, time_suffix):
    """
    GÜNCELLENDİ: Suffix'i dikkate alarak şu an o aralıkta mıyız kontrol eder.
    
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
        
        # hour_str örn: "14:30"
        start_hour = int(hour_str.split(':')[0])
        
        # Dakikayı suffix'ten al (":30" -> 30)
        suffix_minute = int(time_suffix.replace(":", ""))

        # Başlangıç ve Bitiş zamanlarını oluştur
        start_time = now.replace(hour=start_hour, minute=suffix_minute, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1) # 1 saatlik blok varsayımı
        
        return start_time <= now < end_time
    except Exception as e:
        print(f"Zaman kontrol hatası: {e}")
        return False

def create_shadowed_frame(parent, bg="white", shadow_color="#AAAAAA", shadow_x=5, shadow_y=5, bd=1, relief="solid"):
    shadow_frame = tk.Frame(parent, bg=shadow_color)
    content_frame = tk.Frame(shadow_frame, bg=bg, relief=relief, bd=bd)
    content_frame.pack(expand=True, fill="both", padx=(0, shadow_x), pady=(0, shadow_y))
    shadow_frame.content_frame = content_frame
    return shadow_frame

# ----------------------------------------------------------------------
# 4. ANA TKINTER UYGULAMA SINIFI
# ----------------------------------------------------------------------

class RoomScheduleApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Oda Rezervasyon Sistemi")

        # Varsayılan Suffix (API'den gelene kadar)
        self.time_suffix = ":30"
        self.start_hour = 9 
        self.end_hour = 19

        # --- MANUEL TAM EKRAN AYARI ---
        self.app_width = self.winfo_screenwidth()
        self.app_height = self.winfo_screenheight()
        self.geometry(f"{self.app_width}x{self.app_height}+0+0")
        self.overrideredirect(True) 
        self.config(cursor="none")
        self.bind("<Escape>", lambda e: self.quit_app())
        
        print(f"Ekran Boyutu: {self.app_width}x{self.app_height}")

        # --- RENK VE FONT AYARLARI ---
        self.colors = {
            "background": "#F0F0F0",
            "primary": "#33648A",    # Lapis-Lazuli
            "available": "#86BBD8",  # Carolina-blue
            "unavailable": "#8E4162",# Magenta
            "highlight": "#F1C40F",  # Sarı
            "light": "#FFFFFF",
            "dark": "#2C3E50",
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
        self.days_to_display = []
        self.days_tr_turkish = []
        self.date_keys = []
        self.refresh_dates()

        # --- GUI DURUM DEĞİŞKENLERİ ---
        self.day_header_widgets = [] 
        self.schedule_cell_widgets = []
        self.room_name = "Oda Yükleniyor..."
        self.ders_programi = {}
        self.display_mode = "grid"
        self.current_meeting_data = None
        self.qr_image = None
        self.participant_images = [] 
        self.api_queue = queue.Queue() 

        # --- ANA ARAYÜZ DÜZENİ ---
        self.configure(bg=self.colors["background"])
        self.grid_rowconfigure(0, weight=1) 
        self.grid_rowconfigure(1, weight=0, minsize=int(self.app_height * 0.07)) 
        self.grid_columnconfigure(0, weight=1)
        
        self.main_frame = tk.Frame(self, bg=self.colors["background"])
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=3, minsize=int(self.app_width*0.28)) 
        self.main_frame.grid_columnconfigure(1, weight=7) 
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
        
        # ÖNCE SUFFIX ÇEKMEYE ÇALIŞ, SONRA ARAYÜZÜ KUR
        self.fetch_time_format_config()
        self.build_schedule_view()
        
        # Detay Görünümü
        self.detail_view_frame = tk.Frame(self.content_frame, bg=self.colors["background"])
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.build_detail_view()
        self.detail_view_frame.grid_remove()

        # --- PERİYODİK GÖREVLERİ BAŞLAT ---
        self.after(100, self.start_periodic_updates) 
        self.after(100, self.process_api_queue)

    def refresh_dates(self):
        """Tarih listelerini bugüne göre yeniler."""
        start_date = datetime.now()
        self.days_to_display = [(start_date + timedelta(days=i)) for i in range(5)]
        self.days_tr_turkish = [self.dict_tr[d.strftime("%A")] for d in self.days_to_display]
        self.date_keys = [d.strftime("%Y-%m-%d") for d in self.days_to_display]

    def start_periodic_updates(self):
        self.update_footer_clock()       
        self.master_update_loop()        

    def master_update_loop(self):
        """Her 30 saniyede bir veri güncelle."""
        print(f"[{datetime.now()}] Veriler güncelleniyor...")
        self.run_in_thread(self.fetch_qr_token)
        self.run_in_thread(self.fetch_room_name)
        self.run_in_thread(self.update_data)
        self.after(30000, self.master_update_loop)

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def process_api_queue(self):
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
                    self.check_for_current_meeting() 
                elif task_name == "detail_data":
                    self.current_meeting_data = data
                    self.update_detail_widgets(details=True)

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_api_queue)

    # ------------------------------------------------------------------
    # API ÇAĞRI FONKSİYONLARI
    # ------------------------------------------------------------------
    
    def fetch_time_format_config(self):
        """
        GÜNCELLENDİ: API'den time_suffix (örn: :30) bilgisini çeker.
        (Uygulama açılışında senkron çalışır, sonraki güncellemeler gerekirse asenkron yapılabilir)
        """
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, JWT_SECRET, algorithm="HS256")
            url = f"{RASPBERRY_NODE_IP}/getIndexesRasp"
            payload = {"room_id": room_id, "token": encoded_jwt}
            
            response = requests.post(url, json=payload, timeout=3)
            if response.status_code == 200:
                config_data = response.json()
                for item in config_data:
                    if item.get("indexName") == "hour":
                        self.time_suffix = item.get("indexValue", ":30")
                        print(f"✅ Suffix ayarlandı: {self.time_suffix}")
                        return
                    elif item.get("indexName") == "startHour":
                        self.start_hour = int(item.get("indexValue", "9"))
                    elif item.get("indexName") == "endHour":
                        self.end_hour = int(item.get("indexValue", "19"))
            print(f"⚠️ Suffix bulunamadı, varsayılan kullanılıyor: {self.time_suffix}")
        except Exception as e:
            print(f"⚠️ Suffix API hatası: {e}. Varsayılan: {self.time_suffix}")

    def fetch_room_name(self):
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, JWT_SECRET, algorithm="HS256")
            url = f"{RASPBERRY_NODE_IP}/getQRCodeToken"
            headers = {"Content-Type": "application/json"}
            data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "room_name": 1, "accessType": "{ACCESS_TYPE}"}}'
            response = requests.post(url, headers=headers, data=data, timeout=5)
            
            if response.status_code == 200:
                name = response.json().get("room_name")
                self.api_queue.put(("room_name", name))
        except Exception as e:
            pass

    def fetch_qr_token(self):
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, JWT_SECRET, algorithm="HS256")
            url = f"{RASPBERRY_NODE_IP}/getQRCodeToken"
            headers = {"Content-Type": "application/json"}
            data = f'{{"room_id": {room_id}, "token": "{encoded_jwt}", "accessType": "{ACCESS_TYPE}"}}'
            response = requests.post(url, headers=headers, data=data, timeout=5)
            token = response.json().get("token") if response.status_code == 200 else None
            self.api_queue.put(("qr_token", token))
        except Exception as e:
            pass

    def update_data(self):
        try:
            self.refresh_dates()
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, JWT_SECRET, algorithm="HS256")
            payload = {"room_id": room_id, "token": encoded_jwt}
            response = requests.post(f"{RASPBERRY_NODE_IP}/getSchedule", json=payload, timeout=5)
            response.raise_for_status()
            api_response = response.json()
            new_data = api_response[0] if isinstance(api_response, list) and api_response else api_response
            
            # GÜNCELLENDİ: self.time_suffix gönderiliyor
            ders_programi = transform_schedule(new_data, self.date_keys, self.time_suffix, self.start_hour,self.end_hour) 
            self.api_queue.put(("schedule_data", ders_programi))
            
        except Exception as e:
            print(f"⚠️ Takvim güncelleme hatası: {e}")
            pass
            
    def fetch_details_data(self, rendezvous_id):
        try:
            encoded_jwt = jwt.encode({"exp": time.time() + 30}, JWT_SECRET, algorithm="HS256")
            url = f"{RASPBERRY_NODE_IP}/getScheduleDetails"
            headers = {"Content-Type": "application/json"}
            payload = {"room_id": room_id, "token": encoded_jwt, "rendezvous_id": rendezvous_id}
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
            response.raise_for_status()
            self.api_queue.put(("detail_data", response.json()))
        except Exception as e:
            print(f"⚠️ Detay hatası: {e}")
            pass

    def load_image_from_url_pil(self, url, size=(100, 100)):
        try:
            full_url = f"{RASPBERRY_NODE_IP}{url}"
            response = requests.get(full_url, timeout=3)
            response.raise_for_status()
            img_data = io.BytesIO(response.content)
            img = Image.open(img_data).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return self.default_profile_image(size)

    def default_profile_image(self, size=(100, 100)):
        img = Image.new('RGB', size, color=self.colors["primary"])
        return ImageTk.PhotoImage(img)

    # ------------------------------------------------------------------
    # GUI İNŞA FONKSİYONLARI
    # ------------------------------------------------------------------

    def build_qr_card(self):
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
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_rowconfigure(0, weight=1) 
        dikey_padding = int(self.app_height * 0.015)

        info_label = tk.Label(self.footer_frame, text="pve.izu.edu.tr/randevu ← Randevu İçin", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        info_label.grid(row=0, column=0, sticky="w", padx=20, pady=dikey_padding)

        self.clock_label = tk.Label(self.footer_frame, text="⏰ Yükleniyor...", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        self.clock_label.grid(row=0, column=1, sticky="e", padx=20, pady=dikey_padding)

    def build_schedule_view(self):
        """
        Sağ taraftaki Takvim Tablosunu oluşturur.
        GÜNCELLENDİ: self.time_suffix kullanılarak saatler oluşturuluyor.
        """
        self.day_header_widgets = []
        self.schedule_cell_widgets = []
        for _ in range(5):
            self.schedule_cell_widgets.append({})

        # GÜNCELLENDİ: Suffix'i dinamik kullan
        self.hours = [f"{h:02}{self.time_suffix}" for h in range(9, 19)]
        
        grid_frame = self.schedule_view_frame
        
        # Boyut Hesaplamaları
        saat_sutunu_genisligi = int(self.app_width * 0.05)
        icerik_cercevesi_genisligi = (self.app_width * 0.72) - saat_sutunu_genisligi 
        hucre_genisligi = int(icerik_cercevesi_genisligi / 5) - 9 
        toplam_icerik_yuksekligi = int(self.app_height * 0.92) 
        baslik_yuksekligi = int(toplam_icerik_yuksekligi * 0.10)
        kalan_yukseklik = toplam_icerik_yuksekligi - baslik_yuksekligi
        hucre_yuksekligi = int(kalan_yukseklik / len(self.hours))
        
        # Grid Yapılandırması
        grid_frame.grid_rowconfigure(0, weight=0, minsize=baslik_yuksekligi)
        for i in range(len(self.hours)):
            grid_frame.grid_rowconfigure(i + 1, weight=0, minsize=hucre_yuksekligi)
        grid_frame.grid_columnconfigure(0, weight=0, minsize=saat_sutunu_genisligi)
        for i in range(5):
            grid_frame.grid_columnconfigure(i + 1, weight=0, minsize=hucre_genisligi)
            
        # Saat Başlığı
        tk.Label(grid_frame, text="Saat", font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"], relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")
        
        # Gün Başlıkları
        for i in range(5):
            header_cell_frame = tk.Frame(grid_frame, bg=self.colors["primary"], relief="solid", bd=1)
            header_cell_frame.grid(row=0, column=i+1, sticky="nsew")
            header_cell_frame.pack_propagate(False) 

            day_name_label = tk.Label(header_cell_frame, text="", font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"])
            day_name_label.pack(side="top", pady=(5,0))
            
            date_label = tk.Label(header_cell_frame, text="", font=self.fonts["info"], bg=self.colors["primary"], fg=self.colors["white"])
            date_label.pack(side="top")
            
            today_label = tk.Label(header_cell_frame, text="Bugün", font=self.fonts["info"], bg=self.colors["primary"], fg=self.colors["white"])
            
            self.day_header_widgets.append({
                "frame": header_cell_frame, "day_name": day_name_label, "date": date_label, "today": today_label
            })

        # Saatler ve Hücreler
        for j, hour in enumerate(self.hours):
            hour_label = tk.Label(grid_frame, text=hour, font=self.fonts["hour"], bg=self.colors["light"], fg=self.colors["text_primary"], relief="solid", bd=1)
            hour_label.grid(row=j+1, column=0, sticky="nsew")
            self.hour_labels[hour] = hour_label
            
            for i in range(5):
                cell_frame_container = tk.Frame(grid_frame, relief="solid", bd=1)
                cell_frame_container.grid(row=j+1, column=i+1, sticky="nsew")
                cell_frame_container.grid_propagate(False) 
                
                cell_frame = tk.Frame(cell_frame_container, bg=self.colors["available"])
                cell_frame.pack(expand=True, fill="both")

                label1 = tk.Label(cell_frame, text="", font=self.fonts["cell_main"], bg=self.colors["available"], fg=self.colors["white"], justify="center")
                label1.place(relx=0.5, rely=0.35, anchor="center")
                
                label2 = tk.Label(cell_frame, text="", font=self.fonts["cell_sub"], bg=self.colors["available"], fg=self.colors["white"], justify="center")
                label2.place(relx=0.5, rely=0.65, anchor="center")
                
                self.schedule_cell_widgets[i][hour] = {
                    "container": cell_frame_container, "frame": cell_frame, "label1": label1, "label2": label2
                }
            
    def build_detail_view(self):
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
    # GÜNCELLEME VE KONTROL
    # ------------------------------------------------------------------

    def update_qr_image(self, qr_data):
        if not qr_data: qr_data = "API_ERROR"
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            qr_size = int(self.app_width * 0.26)
            img = img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image)
        except Exception:
            pass

    def update_footer_clock(self):
        now = datetime.now()
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")
        self.clock_label.config(text=f"⏰ {date_str}  •  {time_str}")
        self.after(1000, self.update_footer_clock)
        self.check_for_current_meeting()

    def update_schedule_widgets(self):
        if not self.ders_programi: return
            
        today_tr = self.days_tr_turkish[0] 
        # GÜNCELLENDİ: Şu anki saati suffix'e göre oluştur (Vurgulamak için)
        suffix_minute = int(self.time_suffix.replace(":", ""))
        now = datetime.now()
        
        # Eğer şu anki dakika suffix'ten küçükse bir önceki saati highlight et, değilse şu anı.
        # Örnek: Suffix :30. Saat 14:10 -> 13:30 bloğuna (teknik olarak) denk gelebilir ama
        # burada basitçe "o anki blok" mantığı için:
        target_hour = now.hour
        if now.minute < suffix_minute:
            target_hour -= 1
            
        current_hour_str = f"{target_hour:02d}{self.time_suffix}"
        
        for i in range(5):
            day_tr = self.days_tr_turkish[i]
            date_str = self.days_to_display[i].strftime("%d.%m")
            widgets = self.day_header_widgets[i]

            widgets["day_name"].config(text=day_tr)
            widgets["date"].config(text=date_str)

            if i == 0:
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

        for hour, label in self.hour_labels.items():
            if hour == current_hour_str: 
                 label.config(bg=self.colors["highlight"], fg=self.colors["dark"])
            else:
                 label.config(bg=self.colors["light"], fg=self.colors["text_primary"])

        for i in range(5): 
            date_key = self.date_keys[i]
            day_widgets = self.schedule_cell_widgets[i]

            if date_key not in self.ders_programi: 
                continue
            
            for hour in self.hours:
                if hour not in self.ders_programi[date_key]: continue
                
                cell = day_widgets[hour]
                data = self.ders_programi[date_key][hour] 
                status = data["durum"]
                
                if status == "Boş":
                    bg = self.colors["available"]; fg = self.colors["white"]
                    label1_text = "Randevuya"
                    label2_text = "Uygun"
                else:
                    bg = self.colors["unavailable"]; fg = self.colors["white"]
                    raw_activity = data.get("aktivite", "Dolu")
                    raw_person = data.get("düzenleyen", "")

                    MAX_LEN = 14 
                    label1_text = raw_activity[:MAX_LEN] + "..." if len(raw_activity) > MAX_LEN else raw_activity
                    label2_text = f"{raw_person[:MAX_LEN] + '...' if len(raw_person) > MAX_LEN else raw_person}"

                cell["frame"].config(bg=bg)
                cell["label1"].config(text=label1_text, bg=bg, fg=fg)
                cell["label2"].config(text=label2_text, bg=bg, fg=fg)
                
                if hour == current_hour_str and i == 0:
                    cell["container"].config(highlightbackground=self.colors["highlight"], highlightthickness=3, bd=0)
                else:
                    cell["container"].config(highlightthickness=0, bd=1)

    def update_detail_widgets(self, details = False):
        if not self.current_meeting_data: 
            return
        main_data = self.current_meeting_data[0]

        self.detail_title.config(text=main_data.get("title", "Başlıksız"))
        
        # GÜNCELLENDİ: Detayda saat aralığını doğru göster (Örn: 14:30 - 15:30)
        start_time_str = main_data.get('hour', '00:00')
        # Sadece saat kısmını alıp +1 ekleyerek aralık oluşturuyoruz
        try:
            s_hour = int(start_time_str.split(':')[0])
            e_hour = s_hour + 1
            time_display = f"{s_hour:02d}{self.time_suffix} - {e_hour:02d}{self.time_suffix}"
        except:
            time_display = start_time_str

        self.detail_time.config(text=f"Zaman: {time_display}")
        self.detail_desc.config(text=main_data.get("message", "Açıklama yok."))

        for widget in self.participants_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        self.participant_images.clear()
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

    def check_for_current_meeting(self):
        global last_switch_time
        
        if not self.ders_programi:
            return

        found_meeting = False
        today_tr = self.days_tr_turkish[0] 
        today_date_key = self.date_keys[0] 
        
        if today_date_key in self.ders_programi:
            for hour, entry in self.ders_programi[today_date_key].items():
                
                # GÜNCELLENDİ: self.time_suffix gönderiliyor
                if entry["durum"] == "Dolu" and check_if_slot_is_current(today_tr, hour, self.time_suffix):
                    
                    found_meeting = True
                    rendezvous_id = entry["rendezvous_id"]
                    current_id = None

                    if isinstance(self.current_meeting_data, dict):
                        data_list = self.current_meeting_data.get("dataResult", [])
                        if isinstance(data_list, list) and len(data_list) > 0:
                            current_id = data_list[0].get("rendezvous_id")

                    elif isinstance(self.current_meeting_data, list) and len(self.current_meeting_data) > 0:
                        current_id = self.current_meeting_data[0].get("rendezvous_id")

                    if (self.display_mode == "detail" and (datetime.now() - last_switch_time).total_seconds() >= 10):
                        self.show_schedule_view()
                        last_switch_time = datetime.now()

                    if (self.display_mode == "grid" or str(current_id) != str(rendezvous_id)) and (datetime.now() - last_switch_time).total_seconds() >= 30:
                        print(f"Yeni toplantı bulundu: {rendezvous_id}. Detaylar getiriliyor...") 
                        self.show_detail_view(rendezvous_id)
                        last_switch_time = datetime.now()
                    break
                
        if not found_meeting and self.display_mode == "detail":
            self.show_schedule_view()

    def show_schedule_view(self):
        self.detail_view_frame.grid_remove()
        self.schedule_view_frame.grid(row=0, column=0, sticky="nsew")
        self.display_mode = "grid"
        self.current_meeting_data = None

    def show_detail_view(self, rendezvous_id):
        self.schedule_view_frame.grid_remove()
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.display_mode = "detail"
        self.run_in_thread(self.fetch_details_data, rendezvous_id)

    def quit_app(self):
        print("Çıkış yapılıyor...")
        self.destroy()

if __name__ == "__main__": 
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