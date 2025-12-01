#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import font
import requests
from PIL import Image, ImageTk
import io
import time
from datetime import datetime, timedelta
import threading
import queue
import sys

# ----------------------------------------------------------------------
# 1. SABİTLER VE API AYARLARI
# ----------------------------------------------------------------------

RASPBERRY_NODE_IP = 'https://pve.izu.edu.tr/randevu'

# ----------------------------------------------------------------------
# 4. ANA TKINTER UYGULAMA SINIFI
# ----------------------------------------------------------------------

class RoomScheduleApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Döngüsel Oda Ekranı")

        # --- 1. AYARLAR VE BOYUTLAR (OTOMATİK BÜYÜME) ---
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Ekranın %95 genişliği ve %90 yüksekliği
        self.app_width = int(screen_w * 0.90)  
        self.app_height = int(screen_h * 0.90) 
        self.radius_miktari = 30 
        
        # Ekranın ortasında açılması için hesaplama
        pos_x = (screen_w // 2) - (self.app_width // 2)
        pos_y = (screen_h // 2) - (self.app_height // 2)

        # --- 2. RENKLER ---
        self.colors = { 
            "background": "#F0F0F0",    # Tablo Zemini
            "primary": "#6D3AF8",       # Mor Renk
            "available": "#FFFFFF",     # Beyaz
            "unavailable": "#E2E2E2",   # Gri (Dolu Ders)
            "highlight": "#0011FF",     
            "light": "#E4E4E4",         
            "dark": "#2C3E50",          
            "text_primary": "#000000",  
            "white": "#FFFFFF",         
            "app_bg": "#000001",        # ŞEFFAF KODU
        }

        # --- 3. PENCERE YAPILANDIRMASI ---
        self.geometry(f"{self.app_width}x{self.app_height}+{pos_x}+{pos_y}")
        self.overrideredirect(True) # Çerçevesiz Mod
        self.config(cursor="arrow", bg=self.colors["app_bg"]) 
        
        try:
            self.wm_attributes("-transparentcolor", self.colors["app_bg"])
        except Exception:
            pass

        self.bind("<Escape>", lambda e: self.quit_app())
        
        # --- 4. FONTLAR ---
        self.fonts = {
            "title": font.Font(family="Montserrat", size=int(self.app_height * 0.030), weight="bold"),
            "subtitle": font.Font(family="Montserrat", size=int(self.app_height * 0.020), weight="bold"),
            "day": font.Font(family="Montserrat", size=int(self.app_height * 0.022), weight="bold"),
            "hour": font.Font(family="Montserrat", size=int(self.app_height * 0.021)),
            "cell_main": font.Font(family="Montserrat", size=int(self.app_height * 0.020), weight="bold"),
            "cell_sub": font.Font(family="Montserrat", size=int(self.app_height * 0.018)),
            "info": font.Font(family="Montserrat", size=int(self.app_height * 0.016)),
            "footer": font.Font(family="Montserrat", size=int(self.app_height * 0.025)),
        }
        
        # --- 5. ARAYÜZ KATMANLARI ---
        
        # A) En Alt Katman (Şeffaf Canvas)
        self.base_canvas = tk.Canvas(self, bg=self.colors["app_bg"], highlightthickness=0)
        self.base_canvas.pack(fill="both", expand=True)
        self.update_idletasks()
        
        # B) BEYAZ KART (DIŞ ÇERÇEVE)
        self.create_rounded_rect(self.base_canvas, 0, 0, self.app_width, self.app_height, 
                                 radius=self.radius_miktari, 
                                 fill="#FFFFFF", outline="") 

        # C) İÇERİK ÇERÇEVESİ
        self.main_frame = tk.Frame(self.base_canvas, bg=self.colors["background"])
        padding_orani = 0.96 
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", 
                              relwidth=padding_orani, relheight=padding_orani)
        
        self.main_frame.grid_columnconfigure(0, weight=1) 
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0, minsize=int(self.app_height * 0.04)) 
        
        # --- 6. İÇERİK YERLEŞİMİ ---
        
        # Footer
        self.footer_frame = tk.Frame(self.main_frame, bg=self.colors["primary"])
        self.footer_frame.grid(row=1, column=0, sticky="sew")
        self.build_footer()
        
        # Tablo Alanı
        self.content_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.schedule_view_frame = tk.Frame(self.content_frame, bg=self.colors["light"])
        self.schedule_view_frame.grid(row=0, column=0, sticky="nsew")
        
        # --- DEĞİŞKENLER ---
        self.room_list = [f"Oda {i}" for i in range(1, 19)] 
        self.visible_columns = 6  
        self.current_x = 0
        self.target_x = 0 
        
        self.current_page_index = 0 # Sayfa takibi
        self.is_info_mode_active = False # Duyuru modu takibi
        
        self.slide_direction = -1
        self.is_animating = False
        self.ders_programi = {} 
        self.display_mode = "grid"
        self.current_meeting_data = None
        self.api_queue = queue.Queue()
        
        self.schedule_cells = {} 
        self.room_header_labels = {} 
        self.hour_labels = {}
        
        
        self.build_schedule_view()
        self.build_info_panel() 
        
        self.detail_view_frame = tk.Frame(self.content_frame, bg=self.colors["background"])
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.build_detail_view()
        self.detail_view_frame.grid_remove()

        # Başlat
        self.after(100, self.start_periodic_updates)
        self.after(100, self.process_api_queue) 
        self.after(2000, self.start_sliding_cycle)
            
    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)
    
    def start_periodic_updates(self):
        self.update_footer_clock()       
        self.master_update_loop()        

    def master_update_loop(self):
        print(f"[{datetime.now()}] Veri güncelleniyor...")
        self.run_in_thread(self.update_data)
        self.after(30000, self.master_update_loop)

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()
        
    def process_api_queue(self):
        try:
            while not self.api_queue.empty():
                task_name, data = self.api_queue.get_nowait()
                if task_name == "schedule_data":
                    self.ders_programi = data
                    self.update_schedule_widgets()
                elif task_name == "detail_data":
                    self.current_meeting_data = data
        except queue.Empty:
            pass 
        finally:
            self.after(100, self.process_api_queue)
    
    # ------------------------------------------------------------------
    # ANİMASYON VE DÖNGÜ MANTIĞI (SON HALİ)
    # ------------------------------------------------------------------

    def start_sliding_cycle(self):
        """SAYFA -> DUYURU (20sn) -> SAYFA Döngüsü"""
        
       
        if self.is_info_mode_active:
            self.is_info_mode_active = False
            self.info_frame.place_forget()
            self.current_page_index = 0    
            self.target_x = 0
            self.animate_slide()
            self.after(10000, self.start_sliding_cycle)
            return

        
        total_rooms = len(self.room_list)
        total_pages = (total_rooms + self.visible_columns - 1) // self.visible_columns
        
        
        self.current_page_index += 1
        
        if self.current_page_index >= total_pages:
            self.is_info_mode_active = True
            self.target_x = 0
            self.animate_slide()
            self.info_frame.place(x=self.info_panel_x, y=0, width=self.col_width * 4, relheight=1)
            
            # 3. Duyuru Ekranı Süresi
            self.after(20000, self.start_sliding_cycle)
            
        else:
            self.target_x = -(self.current_page_index * self.visible_columns * self.col_width)
            self.animate_slide()
            self.after(10000, self.start_sliding_cycle)

    def animate_slide(self):
        if abs(self.current_x - self.target_x) < 2:
            self.current_x = self.target_x
            self.slider_frame.place(x=self.current_x, y=0)
            return 

        step = (self.target_x - self.current_x) * 0.05
        if abs(step) < 1: step = 1 if self.target_x > self.current_x else -1
            
        self.current_x += step
        self.slider_frame.place(x=self.current_x, y=0)
        self.after(30, self.animate_slide)       
        
    def update_data(self):
        """ TEST VERİSİ ÜRETİR """
        import random
        fake_schedule = {}
        dersler = ["BIM 101", "Matematik", "Fizik", "Toplantı", "Seminer"]
        hocalar = ["A. Yılmaz", "B. Demir", "C. Kaya", "D. Çelik", "Y. Duman", "N. Gürkan"]
        
        for room in self.room_list:
            fake_schedule[room] = {}
            for hour in self.hours:
                if random.random() < 0.3:
                    fake_schedule[room][hour] = {
                        "durum": "Dolu",
                        "aktivite": random.choice(dersler),
                        "düzenleyen": random.choice(hocalar),
                        "rendezvous_id": 999
                    }
                else:
                    fake_schedule[room][hour] = {"durum": "Boş", "aktivite": "", "düzenleyen": "", "rendezvous_id": ""}
        
        self.api_queue.put(("schedule_data", fake_schedule))
            
    def fetch_details_data(self, rendezvous_id):
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
    # GUI İNŞA
    # ------------------------------------------------------------------

    def build_footer(self):
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_rowconfigure(0, weight=1) 
        
        dikey_padding = int(self.app_height * 0.005) 

        info_label = tk.Label(self.footer_frame, text="pve.izu.edu.tr/randevu ← Randevu İçin", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        info_label.grid(row=0, column=0, sticky="w", padx=20, pady=dikey_padding)

        self.clock_label = tk.Label(self.footer_frame, text="⏰ Yükleniyor...", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        self.clock_label.grid(row=0, column=1, sticky="e", padx=20, pady=dikey_padding)

    def build_schedule_view(self):
        """Film Şeridi Mantığı - DÜZELTİLMİŞ (Yükseklik Ayarlı & Beyaz Zemin)"""
        self.hours = [f"{h:02}:00" for h in range(9, 19)]
        
        self.schedule_view_frame.grid_rowconfigure(0, weight=1)
        self.schedule_view_frame.grid_columnconfigure(0, weight=1)
        
        
        self.mask_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["available"], bd=0)
        self.slider_frame = tk.Frame(self.mask_frame, bg=self.colors["available"])
        self.slider_frame.place(x=0, y=0, relheight=1)
        
        # --- GENİŞLİK HESABI ---
        real_width = self.app_width * 0.96 
        screen_width = int(real_width)
        
        saat_genisligi = int(screen_width * 0.05)
        available_width = screen_width - saat_genisligi
        self.col_width = int(available_width / self.visible_columns)
        
        # DÜZELTME: Yükseklik %88'e çekildi (Footer altında kalmaması için)
        toplam_yukseklik = int(self.app_height * 0.88)
        
        baslik_yuk = int(toplam_yukseklik * 0.08)
        hucre_yuk = int((toplam_yukseklik - baslik_yuk) / len(self.hours))
        
        self.mask_frame.place(x=saat_genisligi, y=0, width=available_width, relheight=1)
        
        # Sol Taraf (Saat Sütunu) - Beyaz Zemin
        self.fixed_hour_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["available"], width=saat_genisligi, bd=0)
        self.fixed_hour_frame.place(x=0, y=0, width=saat_genisligi, relheight=1)
        self.fixed_hour_frame.pack_propagate(False)
        self.fixed_hour_frame.grid_columnconfigure(0, weight=1)
        
        self.fixed_hour_frame.grid_rowconfigure(0, minsize=baslik_yuk, weight=0)
        tk.Label(self.fixed_hour_frame, text="Saat", font=self.fonts["day"], bg=self.colors["primary"], fg=self.colors["white"], relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")
        
        for j, hour in enumerate(self.hours):
            self.fixed_hour_frame.grid_rowconfigure(j+1, minsize=hucre_yuk, weight=1)
            tk.Label(self.fixed_hour_frame, text=hour, font=self.fonts["hour"], bg=self.colors["available"], fg=self.colors["text_primary"], relief="solid", bd=1).grid(row=j+1, column=0, sticky="nsew")

        # --- SLIDER FRAME ---
        self.slider_frame.grid_rowconfigure(0, minsize=baslik_yuk, weight=0)
        for i in range(len(self.hours)):
            self.slider_frame.grid_rowconfigure(i+1, minsize=hucre_yuk, weight=1)
            
        header_font = font.Font(family="Arial", size=int(self.app_height * 0.020), weight="bold")
        main_font = font.Font(family="Arial", size=int(self.app_height * 0.016), weight="bold")
        sub_font = font.Font(family="Arial", size=int(self.app_height * 0.014))
        
        for col_idx, room_name in enumerate(self.room_list):
            self.slider_frame.grid_columnconfigure(col_idx, minsize=self.col_width, weight=0, uniform="cols")
            
            header_cell = tk.Frame(self.slider_frame, bg=self.colors["primary"], relief="solid", bd=1)
            header_cell.grid(row=0, column=col_idx, sticky="nsew")
            tk.Label(header_cell, text=room_name, font=header_font, bg=self.colors["primary"], fg=self.colors["white"]).pack(expand=True)
            
            for row_idx, hour in enumerate(self.hours):
                cell_container = tk.Frame(self.slider_frame, relief="solid", bd=1)
                cell_container.grid(row=row_idx+1, column=col_idx, sticky="nsew")
                cell_container.grid_propagate(False)
                
                cell_frame = tk.Frame(cell_container, bg=self.colors["available"])
                cell_frame.pack(expand=True, fill="both")
                
                lbl1 = tk.Label(cell_frame, text="", font=main_font, bg=self.colors["available"], fg=self.colors["white"], wraplength=self.col_width*0.9)
                lbl1.place(relx=0.5, rely=0.35, anchor="center")
                
                lbl2 = tk.Label(cell_frame, text="", font=sub_font, bg=self.colors["available"], fg=self.colors["white"], wraplength=self.col_width*0.9)
                lbl2.place(relx=0.5, rely=0.65, anchor="center")
                
                self.schedule_cells[room_name] = self.schedule_cells.get(room_name, {})
                self.schedule_cells[room_name][hour] = {"container": cell_container, "frame": cell_frame, "label1": lbl1, "label2": lbl2}

    def build_info_panel(self):
        """Duyuru Ekranını oluşturur ama gizli tutar."""
        panel_width = self.col_width * 4
        self.info_panel_x = self.col_width * 2
        self.info_frame = tk.Frame(self.mask_frame, bg=self.colors["primary"])
        
        lbl_title = tk.Label(self.info_frame, text="DUYURULAR & ETKİNLİKLER", 
                             font=self.fonts["title"], bg=self.colors["primary"], fg=self.colors["white"])
        lbl_title.pack(pady=(40, 20))
        
        img_placeholder = tk.Label(self.info_frame, text="[GÖRSEL ALANI]", 
                                   bg=self.colors["dark"], fg=self.colors["white"], 
                                   font=self.fonts["subtitle"])
        img_placeholder.pack(fill="both", expand=True, padx=40, pady=20)
        
        lbl_desc = tk.Label(self.info_frame, 
                            text="Bu alana üniversite ile ilgili önemli duyurular, etkinlik haberleri veya günün menüsü gelecek.\nAPI entegrasyonu yapıldığında burası otomatik değişecek.", 
                            font=self.fonts["cell_main"], bg=self.colors["primary"], fg=self.colors["white"], wraplength=panel_width-80)
        lbl_desc.pack(pady=(0, 40))

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
        self.participant_images = []

    def update_footer_clock(self):
        now = datetime.now()
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        gun_ismi = gunler[now.weekday()]
        
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")
        
        self.clock_label.config(text=f"⏰ {date_str} {gun_ismi}   •   {time_str}")
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
                    bg = self.colors["available"]; fg = self.colors["white"]
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