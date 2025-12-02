#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import font
import threading
import queue
from datetime import datetime
import time
import requests
import json

# ----------------------------------------------------------------------
# 1. AYARLAR VE UYGULAMA
# ----------------------------------------------------------------------

# API AYARLARI
API_BASE_URL = "http://localhost:3000"
DEVICE_ROOM_ID = 1  
API_TOKEN = "token"

class RoomScheduleApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Döngüsel Oda Ekranı")

        # --- EKRAN AYARLARI ---
        self.attributes('-fullscreen', True)
        self.update_idletasks()
        self.app_width = self.winfo_screenwidth()
        self.app_height = self.winfo_screenheight()
        
        self.bind("<Escape>", lambda e: self.quit_app())

        # --- BOYUTLAR ---
        self.footer_height = int(self.app_height * 0.08)
        self.table_area_height = self.app_height - self.footer_height
        
        # Kenar boşlukları ve Radius
        self.margin_x = 25 
        self.margin_y = 25
        self.radius_miktari = 35

        # --- RENKLER ---
        self.colors = {
            "app_bg": "#FFFFFF",        # Kenar boşlukları (BEYAZ)
            "content_bg": "#F0F0F0",    # Tablo zemini
            "primary": "#6D3AFF",       # Mor Renk
            "available": "#FFFFFF",     
            "unavailable": "#E2E2E2",   
            "highlight": "#0011FF",
            "light": "#E4E4E4",
            "dark": "#2C3E50",
            "text_primary": "#000000",
            "white": "#FFFFFF",
        }
        
        self.config(bg=self.colors["app_bg"], cursor="none")

        # --- FONTLAR ---
        self.fonts = {
            "title": font.Font(family="Montserrat", size=int(self.app_height * 0.030), weight="bold"),
            "subtitle": font.Font(family="Montserrat", size=int(self.app_height * 0.020), weight="bold"),
            "day": font.Font(family="Montserrat", size=int(self.app_height * 0.022), weight="bold"),
            "hour": font.Font(family="Montserrat", size=int(self.app_height * 0.021)),
            "cell_main": font.Font(family="Montserrat", size=int(self.app_height * 0.020), weight="bold"),
            "cell_sub": font.Font(family="Montserrat", size=int(self.app_height * 0.018)),
            "info": font.Font(family="Montserrat", size=int(self.app_height * 0.016)),
            "footer": font.Font(family="Montserrat", size=int(self.app_height * 0.020)),
            "footer_bold": font.Font(family="Montserrat", size=int(self.app_height * 0.025), weight="bold"),
        }

        # --- GUI KATMANLARI ---

        # 1. FOOTER
        self.footer_frame = tk.Frame(self, bg=self.colors["primary"], height=self.footer_height)
        self.footer_frame.place(x=0, y=self.app_height - self.footer_height, width=self.app_width, height=self.footer_height)
        self.footer_frame.pack_propagate(False)
        self.build_footer()

        # 2. TABLO ALANI
        self.container_canvas = tk.Canvas(self, bg=self.colors["app_bg"], highlightthickness=0, bd=0)
        self.container_canvas.place(x=0, y=0, width=self.app_width, height=self.table_area_height)

        # Kart Çizimi
        rect_x1, rect_y1 = self.margin_x, self.margin_y
        rect_x2 = self.app_width - self.margin_x
        rect_y2 = self.table_area_height - self.margin_y

        self.create_rounded_rect(self.container_canvas, rect_x1, rect_y1, rect_x2, rect_y2,
                                 radius=self.radius_miktari,
                                 fill=self.colors["content_bg"], outline="")

        # 3. İÇERİK ÇERÇEVESİ
        self.content_frame = tk.Frame(self.container_canvas, bg=self.colors["content_bg"], bd=0)
        
        inset = 2
        content_w = rect_x2 - rect_x1 - (inset*2)
        content_h = rect_y2 - rect_y1 - (inset*2)
        content_x = rect_x1 + inset
        content_y = rect_y1 + inset
        
        self.container_canvas.create_window(content_x, content_y, window=self.content_frame, anchor="nw", width=content_w, height=content_h)

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.content_area_width = content_w 
        self.content_area_height = content_h

        # Tablo Görünümü
        self.schedule_view_frame = tk.Frame(self.content_frame, bg=self.colors["content_bg"])
        self.schedule_view_frame.grid(row=0, column=0, sticky="nsew")

        # --- MANTIK DEĞİŞKENLERİ ---
        
        self.room_list = [] 
        self.room_extensions = []
        self.room_map = {} 
        self.building_name = ""
        
        self.visible_columns = 4   
        self.info_mode_active = False 
        self.announcement_data = None 
        
        self.current_col_index = 0
        self.current_x = 0
        self.target_x = 0

        self.ders_programi = {}
        self.api_queue = queue.Queue()
        self.schedule_cells = {}
        
        self.hours = [f"{h:02}:00" for h in range(9, 19)]
        
        self.build_info_panel_overlay()

        self.detail_view_frame = tk.Frame(self.content_frame, bg=self.colors["content_bg"])
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.build_detail_view()
        self.detail_view_frame.grid_remove()

        # --- BAŞLATMA SIRASI ---
        self.after(100, self.start_initial_setup) 
        self.after(100, self.process_api_queue)

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def start_initial_setup(self):
        """Uygulama açılırken ilk önce odaları öğrenir."""
        print("API: Bina ve oda bilgileri çekiliyor...")
        self.run_in_thread(self.fetch_building_details)

    def fetch_building_details(self):
        """API /getBuildingDetails çağrısı"""
        try:
            headers = {'x-hardware-token': API_TOKEN, 'Content-Type': 'application/json'}
            payload = {'room_id': DEVICE_ROOM_ID}
            
            response = requests.post(f"{API_BASE_URL}/getBuildingDetails", json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rooms_data = data.get("rooms", [])
                
                b_details = data.get("buildingDetails", [])
                fetched_building_name = "BİLİNMEYEN BİNA"
                if b_details and len(b_details) > 0:
                    fetched_building_name = b_details[0].get("building_name", "")

                new_room_list = []
                new_room_extensions = []
                new_room_map = {}
                
                for r in rooms_data:
                    r_name = r.get("room_name", "Bilinmeyen Oda")
                    r_id = r.get("room_id")
                    r_desc = r.get("roomDesc", "") 
                    
                    new_room_list.append(r_name)
                    new_room_extensions.append(r_desc)
                    if r_id:
                        new_room_map[r_id] = r_name
                
                self.api_queue.put(("setup_rooms", (new_room_list, new_room_extensions, new_room_map, fetched_building_name)))
            else:
                print(f"API Hatası: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Bağlantı Hatası (Details): {e}")

    def start_periodic_updates(self):
        self.update_footer_clock()
        self.master_update_loop()
        self.start_sliding_cycle() 

    def master_update_loop(self):
        print(f"[{datetime.now()}] Takvim güncelleniyor...")
        self.run_in_thread(self.update_data)
        self.after(30000, self.master_update_loop)

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def process_api_queue(self):
        try:
            while not self.api_queue.empty():
                task_name, data = self.api_queue.get_nowait()
                
                if task_name == "setup_rooms":
                    self.room_list, self.room_extensions, self.room_map, b_name = data
                    self.building_name = b_name
            
                    self.building_label.config(text=self.building_name)
                    
                    self.build_schedule_view() 
                    self.start_periodic_updates() 
                    
                elif task_name == "schedule_data":
                    self.ders_programi = data
                    self.update_schedule_widgets()
                    
                elif task_name == "detail_data":
                    self.current_meeting_data = data
                    
                elif task_name == "announcement_data":
                    self.announcement_data = data
                    
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_api_queue)

    # ------------------------------------------------------------------
    # DÖNGÜ MANTIĞI
    # ------------------------------------------------------------------

    def start_sliding_cycle(self):
        if not self.room_list: return 

        total_rooms = len(self.room_list)
        
        current_step_check = 2 if self.info_mode_active else 4
        next_index = self.current_col_index + current_step_check
        
        if next_index >= total_rooms:
            self.current_col_index = 0
            self.target_x = 0
            
            if self.announcement_data and not self.info_mode_active:
                self.info_mode_active = True
                self.show_info_overlay()
            else:
                self.info_mode_active = False
                self.hide_info_overlay()

            self.animate_slide()
            self.after(2000, self.start_sliding_cycle) 
            return
        
        if self.info_mode_active:
            step = 2        
            wait_time = 4000
        else:
            step = 4        
            wait_time = 8000

        self.current_col_index += step
        self.target_x = -(self.current_col_index * self.col_width)
        
        self.animate_slide()
        self.after(wait_time, self.start_sliding_cycle)

    def show_info_overlay(self):
        """Duyuru panelini sağ tarafta görünür yapar."""
        overlay_x = self.col_width * 2.3      
        overlay_width = self.col_width * 2.2 
        
        self.info_frame.place(x=overlay_x, y=0, width=overlay_width, relheight=1)
        self.info_frame.lift() 

    def hide_info_overlay(self):
        """Duyuru panelini gizler."""
        self.info_frame.place_forget()

    def animate_slide(self):
        if abs(self.current_x - self.target_x) < 2:
            self.current_x = self.target_x
            self.slider_frame.place(x=self.current_x, y=0)
            return

        diff = self.target_x - self.current_x
        step = diff * 0.1 
        
        if abs(step) < 1: step = 1 if diff > 0 else -1

        self.current_x += step
        self.slider_frame.place(x=self.current_x, y=0)
        self.after(20, self.animate_slide)

    def update_data(self):
        """API /getBuildingSchedule çağrısı"""
        try:
            headers = {'x-hardware-token': API_TOKEN, 'Content-Type': 'application/json'}
            payload = {'room_id': DEVICE_ROOM_ID}
            
            response = requests.post(f"{API_BASE_URL}/getBuildingSchedule", json=payload, headers=headers, timeout=10)
            
            real_schedule = {}
            
            for room in self.room_list:
                real_schedule[room] = {}
                for hour in self.hours:
                    real_schedule[room][hour] = {"durum": "Boş", "aktivite": "", "düzenleyen": "", "rendezvous_id": ""}

            if response.status_code == 200:
                data = response.json()
                schedule_list = data.get("schedule", [])
                
                for item in schedule_list:
                    r_id = item.get("room_id")
                    hour_raw = item.get("hour")
                    
                    if hour_raw:
                        hour_fmt = str(hour_raw)[:5] 
                    else:
                        continue
                        
                    activity = item.get("title", "Dolu")
                    organizer = item.get("fullName", "")
                    rendezvous_id = item.get("rendezvous_id")
                    
                    room_name = self.room_map.get(r_id)
                    
                    if room_name and room_name in real_schedule:
                        if hour_fmt in real_schedule[room_name]:
                            real_schedule[room_name][hour_fmt] = {
                                "durum": "Dolu",
                                "aktivite": activity,
                                "düzenleyen": organizer,
                                "rendezvous_id": rendezvous_id
                            }

                self.api_queue.put(("schedule_data", real_schedule))
                
                veri_var_mi = True
                if veri_var_mi:
                    fake_announcement = {"title": "Test Duyurusu", "desc": "İçerik..."}
                    self.api_queue.put(("announcement_data", fake_announcement))
                else:
                    self.api_queue.put(("announcement_data", None))
                    
            else:
                print(f"Schedule API Hatası: {response.status_code}")

        except Exception as e:
            print(f"Schedule Bağlantı Hatası: {e}")

    def fetch_details_data(self, rendezvous_id):
        pass

    # ------------------------------------------------------------------
    # GUI İNŞA
    # ------------------------------------------------------------------

    def build_footer(self):
        
        self.footer_frame.grid_columnconfigure(0, weight=1) # Sol (Web)
        self.footer_frame.grid_columnconfigure(1, weight=2) # Orta (Bina Adı - Daha geniş)
        self.footer_frame.grid_columnconfigure(2, weight=1) # Sağ (Saat)
        self.footer_frame.grid_rowconfigure(0, weight=1)

        # SOL: Web Sitesi
        info_label = tk.Label(self.footer_frame, text="pve.izu.edu.tr/randevu ← Randevu İçin", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        info_label.grid(row=0, column=0, sticky="w", padx=30)

        # ORTA: Bina Adı 
        self.building_label = tk.Label(self.footer_frame, text="", font=self.fonts["footer_bold"], bg=self.colors["primary"], fg=self.colors["white"])
        self.building_label.grid(row=0, column=1, sticky="nsew")

        # SAĞ: Saat
        self.clock_label = tk.Label(self.footer_frame, text="⏰ Yükleniyor...", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        self.clock_label.grid(row=0, column=2, sticky="e", padx=30)

    def build_schedule_view(self):
        if hasattr(self, 'slider_frame'):
            for widget in self.slider_frame.winfo_children():
                widget.destroy()
        
        self.schedule_view_frame.grid_rowconfigure(0, weight=1)
        self.schedule_view_frame.grid_columnconfigure(0, weight=1)

        screen_width = self.content_area_width
        screen_height = self.content_area_height

        if not hasattr(self, 'mask_frame'):
            self.mask_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["content_bg"], bd=0)
            self.slider_frame = tk.Frame(self.mask_frame, bg=self.colors["content_bg"])
            self.slider_frame.place(x=0, y=0, relheight=1)

        # --- GENİŞLİK HESABI ---
        saat_genisligi = int(screen_width * 0.05)
        available_width = screen_width - saat_genisligi
        self.col_width = int(available_width / self.visible_columns)

        baslik_yuk = int(screen_height * 0.08)
        hucre_yuk = int((screen_height - baslik_yuk) / len(self.hours))

        self.mask_frame.place(x=saat_genisligi, y=0, width=available_width, relheight=1)

        # SABİT SAAT SÜTUNU
        if not hasattr(self, 'fixed_hour_frame'):
            self.fixed_hour_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["content_bg"], width=saat_genisligi, bd=0)
            self.fixed_hour_frame.place(x=0, y=0, width=saat_genisligi, relheight=1)
            self.fixed_hour_frame.pack_propagate(False)
            self.fixed_hour_frame.grid_columnconfigure(0, weight=1)

            self.fixed_hour_frame.grid_rowconfigure(0, minsize=baslik_yuk, weight=0)
            tk.Label(self.fixed_hour_frame, text="Saat", font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"], relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")

            for j, hour in enumerate(self.hours):
                self.fixed_hour_frame.grid_rowconfigure(j+1, minsize=hucre_yuk, weight=1)
                tk.Label(self.fixed_hour_frame, text=hour, font=self.fonts["hour"], bg=self.colors["content_bg"], fg=self.colors["text_primary"], relief="solid", bd=1).grid(row=j+1, column=0, sticky="nsew")

        # --- SLIDER FRAME İÇERİĞİ ---
        self.slider_frame.grid_rowconfigure(0, minsize=baslik_yuk, weight=0)
        for i in range(len(self.hours)):
            self.slider_frame.grid_rowconfigure(i+1, minsize=hucre_yuk, weight=1)

        header_font = font.Font(family="Arial", size=int(self.app_height * 0.016), weight="bold")
        ext_font = font.Font(family="Arial", size=int(self.app_height * 0.012)) 
        main_font = font.Font(family="Arial", size=int(self.app_height * 0.016), weight="bold")
        sub_font = font.Font(family="Arial", size=int(self.app_height * 0.014))

        for col_idx, room_name in enumerate(self.room_list):
            self.slider_frame.grid_columnconfigure(col_idx, minsize=self.col_width, weight=0, uniform="cols")

            header_cell = tk.Frame(self.slider_frame, bg=self.colors["primary"], relief="solid", bd=1)
            header_cell.grid(row=0, column=col_idx, sticky="nsew")
            
            # --- DEĞİŞİKLİK BURADA YAPILDI ---
            # Önce Dahili Numarayı (Varsa) üstte göster
            if col_idx < len(self.room_extensions):
                ext_num = self.room_extensions[col_idx]
                if ext_num: 
                    tk.Label(header_cell, text=f"Dahili: {ext_num}", font=ext_font, bg=self.colors["primary"], fg=self.colors["light"]).pack(expand=True, fill="x", pady=(5,0))
            
            # Sonra Oda İsmini altta göster
            tk.Label(header_cell, text=room_name, font=header_font, bg=self.colors["primary"], fg=self.colors["white"], wraplength=self.col_width*0.95).pack(expand=True, fill="x", pady=(0,5))
            # ---------------------------------

            for row_idx, hour in enumerate(self.hours):
                cell_container = tk.Frame(self.slider_frame, relief="solid", bd=1)
                cell_container.grid(row=row_idx+1, column=col_idx, sticky="nsew")
                cell_container.grid_propagate(False)

                cell_frame = tk.Frame(cell_container, bg=self.colors["available"])
                cell_frame.pack(expand=True, fill="both")

                lbl1 = tk.Label(cell_frame, text="", font=main_font, bg=self.colors["available"], fg=self.colors["text_primary"], wraplength=self.col_width*0.9)
                lbl1.place(relx=0.5, rely=0.35, anchor="center")

                lbl2 = tk.Label(cell_frame, text="", font=sub_font, bg=self.colors["available"], fg=self.colors["text_primary"], wraplength=self.col_width*0.9)
                lbl2.place(relx=0.5, rely=0.65, anchor="center")

                self.schedule_cells[room_name] = self.schedule_cells.get(room_name, {})
                self.schedule_cells[room_name][hour] = {"container": cell_container, "frame": cell_frame, "label1": lbl1, "label2": lbl2}

    def build_info_panel_overlay(self):
        if hasattr(self, 'info_frame'): self.info_frame.destroy()
            
        self.info_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["content_bg"], relief="solid", bd=0)
        
        # İçerik kutusu
        content_box = tk.Frame(self.info_frame, bg=self.colors["primary"])
        content_box.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_title = tk.Label(content_box, text="DUYURULAR & ETKİNLİKLER",
                             font=self.fonts["title"], bg=self.colors["primary"], fg=self.colors["white"])
        lbl_title.pack(pady=(40, 20))

        img_placeholder = tk.Label(content_box, text="[GÖRSEL ALANI]",
                                   bg=self.colors["dark"], fg=self.colors["white"],
                                   font=self.fonts["subtitle"])
        img_placeholder.pack(fill="both", expand=True, padx=50, pady=20)

        lbl_desc = tk.Label(content_box,
                            text="Bu alana üniversite ile ilgili önemli duyurular, etkinlik haberleri veya günün menüsü gelecek.\nAPI entegrasyonu yapıldığında burası otomatik değişecek.",
                            font=self.fonts["cell_main"], bg=self.colors["primary"], fg=self.colors["white"], wraplength=self.app_width*0.4) 
        lbl_desc.pack(pady=(0, 40))

    def build_detail_view(self):
        frame = self.detail_view_frame
        
        box_width_ratio = 0.6 
        start_x = (1 - box_width_ratio) / 2
        
        # --- 1. DETAY KUTUSU ---
        detail_box = tk.Frame(frame, bg=self.colors["light"], relief="solid", bd=2)
        detail_box.place(relx=start_x, rely=0.1, relwidth=box_width_ratio)
        detail_box.grid_columnconfigure(0, weight=1)

        self.detail_title = tk.Label(detail_box, text="Toplantı Başlığı", font=self.fonts["title"], bg=self.colors["primary"], fg=self.colors["white"])
        self.detail_title.grid(row=0, column=0, sticky="ew", ipady=10)

        self.detail_time = tk.Label(detail_box, text="Zaman: 00:00", font=self.fonts["cell_main"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="w")
        self.detail_time.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        text_wrap_limit = self.content_area_width * box_width_ratio * 0.9
        
        self.detail_desc = tk.Label(detail_box, text="Açıklama...", font=self.fonts["cell_sub"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="nw", justify="left",
                                    wraplength=text_wrap_limit)
        self.detail_desc.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

        # --- 2. KATILIMCILAR ALANI ---
        self.participants_frame = tk.Frame(frame, bg=self.colors["content_bg"])
        self.participants_frame.place(relx=start_x, rely=0.5, relwidth=box_width_ratio)
        
        tk.Label(self.participants_frame, text="Katılımcılar", font=self.fonts["subtitle"], bg=self.colors["content_bg"]).pack()
        self.participant_images = []

    def update_footer_clock(self):
        now = datetime.now()
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        gun_ismi = gunler[now.weekday()]

        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")

        self.clock_label.config(text=f"⏰ {date_str} {gun_ismi}     •     {time_str}")
        self.after(1000, self.update_footer_clock)

    def update_schedule_widgets(self):
        if not self.ders_programi: return
        current_hour_str = f"{datetime.now().hour:02d}:00"

        for room_name in self.room_list:
            if room_name not in self.ders_programi: continue

            for hour in self.hours:
                if hour not in self.ders_programi[room_name]: continue

                cell = self.schedule_cells[room_name][hour]
                data = self.ders_programi[room_name][hour]
                status = data["durum"]

                if status == "Boş":
                    bg = self.colors["available"]; fg = self.colors["text_primary"]
                    l1 = ""; l2 = ""
                else:
                    bg = self.colors["unavailable"]; fg = self.colors["text_primary"]
                    l1 = data.get("aktivite", "Dolu")
                    l2 = data.get("düzenleyen", "")

                cell["frame"].config(bg=bg)
                cell["label1"].config(text=l1, bg=bg, fg=fg)
                cell["label2"].config(text=l2, bg=bg, fg=fg)

                if hour == current_hour_str:
                    cell["container"].config(highlightbackground=self.colors["highlight"], highlightthickness=2, bd=0)
                else:
                    cell["container"].config(highlightthickness=0, bd=1)

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
    app = RoomScheduleApp()
    app.mainloop()