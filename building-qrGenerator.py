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
import os

# ----------------------------------------------------------------------
# 1. AYARLAR
# ----------------------------------------------------------------------

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
            "footer": font.Font(family="Montserrat", size=int(self.app_height * 0.025)),
        }

        # --- GUI KATMANLARI ---

        # 1. FOOTER (En Alt - Sabit)
        self.footer_frame = tk.Frame(self, bg=self.colors["primary"], height=self.footer_height)
        self.footer_frame.place(x=0, y=self.app_height - self.footer_height, width=self.app_width, height=self.footer_height)
        self.footer_frame.pack_propagate(False)
        self.build_footer()

        # 2. TABLO ALANI (Radiuslu Kart)
        self.container_canvas = tk.Canvas(self, bg=self.colors["app_bg"], highlightthickness=0, bd=0)
        self.container_canvas.place(x=0, y=0, width=self.app_width, height=self.table_area_height)

        # Kart Çizimi
        rect_x1, rect_y1 = self.margin_x, self.margin_y
        rect_x2 = self.app_width - self.margin_x
        rect_y2 = self.table_area_height - self.margin_y

        self.create_rounded_rect(self.container_canvas, rect_x1, rect_y1, rect_x2, rect_y2,
                                 radius=self.radius_miktari,
                                 fill=self.colors["content_bg"], outline="")

        # 3. İÇERİK ÇERÇEVESİ (Kartın İçine Gömülü)
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
        self.room_list = [f"Oda {i}" for i in range(1, 19)] # 18 Oda
        
        self.visible_columns = 6   # Ekranda 6 sütun var
        self.info_mode_active = False # Duyuru modu açık mı?
        
        self.current_col_index = 0
        self.current_x = 0
        self.target_x = 0

        self.ders_programi = {}
        self.api_queue = queue.Queue()
        self.schedule_cells = {}
        
        self.build_schedule_view()
        
        # DUYURU PANELİ (Overlay olarak hazırlanır ama gizlidir)
        self.build_info_panel_overlay()

        self.detail_view_frame = tk.Frame(self.content_frame, bg=self.colors["content_bg"])
        self.detail_view_frame.grid(row=0, column=0, sticky="nsew")
        self.build_detail_view()
        self.detail_view_frame.grid_remove()

        # Başlat
        self.after(100, self.start_periodic_updates)
        self.after(100, self.process_api_queue)
        self.after(3000, self.start_sliding_cycle)

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
    # DÖNGÜ MANTIĞI (SPLIT SCREEN HIBRIT MOD)
    # ------------------------------------------------------------------

    def start_sliding_cycle(self):
        total_rooms = len(self.room_list)
        
        # Mod'a göre adım sayısı ve bekleme süresi belirle
        if not self.info_mode_active:
            # NORMAL MOD: 6'şar 6'şar kayar, panel gizli
            step = 6
            wait_time = 8000 # 8 saniye bekle
        else:
            # DUYURU MODU: 2'şer 2'şer kayar (Sol taraftaki boşlukta)
            step = 2
            wait_time = 4000 # 4 saniye bekle (daha seri)

        # Yeni pozisyonu hesapla
        next_index = self.current_col_index + step
        
        # Listenin sonuna geldik mi?
        if next_index >= total_rooms:
            # BAŞA SARMA ZAMANI
            self.current_col_index = 0
            self.target_x = 0
            
            # Eğer Normal Moddaysak -> Duyuru Moduna Geç
            if not self.info_mode_active:
                self.info_mode_active = True
                self.show_info_overlay() # Paneli sağdan çıkar
            
            # Eğer Duyuru Modundaysak -> Normal Moda Dön (Döngü tamamlandı)
            else:
                self.info_mode_active = False
                self.hide_info_overlay() # Paneli gizle

            self.animate_slide()
            self.after(2000, self.start_sliding_cycle) # Geçişte kısa bekleme
            return

        # Normal kaydırma devam ediyor
        self.current_col_index = next_index
        self.target_x = -(self.current_col_index * self.col_width)
        
        self.animate_slide()
        self.after(wait_time, self.start_sliding_cycle)

    def show_info_overlay(self):
        """Duyuru panelini sağ tarafta görünür yapar."""
        # Hesaplama: Sol tarafta 2 sütun (visible_cols / 3) boş kalsın, geri kalanı kapla.
        # Overlay genişliği = 4 sütun genişliği
        overlay_width = self.col_width * 4.2
        
        # X Konumu = 2 sütun genişliğinden sonrası
        overlay_x = self.col_width * 2.3
        
        # Place ile yerleştir (Diğer frame'lerin üzerine biner)
        self.info_frame.place(x=overlay_x, y=0, width=overlay_width, relheight=1)
        self.info_frame.lift() # En üste çıkart

    def hide_info_overlay(self):
        """Duyuru panelini gizler."""
        self.info_frame.place_forget()

    def animate_slide(self):
        if abs(self.current_x - self.target_x) < 2:
            self.current_x = self.target_x
            self.slider_frame.place(x=self.current_x, y=0)
            return

        diff = self.target_x - self.current_x
        step = diff * 0.1 # Yumuşak geçiş
        
        if abs(step) < 1: step = 1 if diff > 0 else -1

        self.current_x += step
        self.slider_frame.place(x=self.current_x, y=0)
        self.after(20, self.animate_slide)

    def update_data(self):
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

    # ------------------------------------------------------------------
    # GUI İNŞA
    # ------------------------------------------------------------------

    def build_footer(self):
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_rowconfigure(0, weight=1)

        info_label = tk.Label(self.footer_frame, text="pve.izu.edu.tr/randevu ← Randevu İçin", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        info_label.grid(row=0, column=0, sticky="w", padx=30)

        self.clock_label = tk.Label(self.footer_frame, text="⏰ Yükleniyor...", font=self.fonts["footer"], bg=self.colors["primary"], fg=self.colors["light"])
        self.clock_label.grid(row=0, column=1, sticky="e", padx=30)

    def build_schedule_view(self):
        self.hours = [f"{h:02}:00" for h in range(9, 19)]

        self.schedule_view_frame.grid_rowconfigure(0, weight=1)
        self.schedule_view_frame.grid_columnconfigure(0, weight=1)

        screen_width = self.content_area_width
        screen_height = self.content_area_height

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

                lbl1 = tk.Label(cell_frame, text="", font=main_font, bg=self.colors["available"], fg=self.colors["text_primary"], wraplength=self.col_width*0.9)
                lbl1.place(relx=0.5, rely=0.35, anchor="center")

                lbl2 = tk.Label(cell_frame, text="", font=sub_font, bg=self.colors["available"], fg=self.colors["text_primary"], wraplength=self.col_width*0.9)
                lbl2.place(relx=0.5, rely=0.65, anchor="center")

                self.schedule_cells[room_name] = self.schedule_cells.get(room_name, {})
                self.schedule_cells[room_name][hour] = {"container": cell_container, "frame": cell_frame, "label1": lbl1, "label2": lbl2}

    def build_info_panel_overlay(self):
        """Bu frame başta gizlidir. Çağrıldığında sağa yerleşir."""
        # Parent olarak schedule_view_frame kullanıyoruz ki tablonun üstüne binsin
        self.info_frame = tk.Frame(self.schedule_view_frame, bg=self.colors["content_bg"], relief="solid", bd=0)
        
        # İçerik kutusu (Duyuru Detayları)
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
                            font=self.fonts["cell_main"], bg=self.colors["primary"], fg=self.colors["white"], wraplength=self.app_width*0.4) # Genişlik ayarlı
        lbl_desc.pack(pady=(0, 40))

    def build_detail_view(self):
        frame = self.detail_view_frame
        
        # --- AYARLAR ---
        # Genişlik oranı: 0.6 (%60). Daraltmak için bunu düşür (örn: 0.5)
        box_width_ratio = 0.6 
        # Ortalamak için X konumu: (1 - 0.6) / 2 = 0.2
        start_x = (1 - box_width_ratio) / 2
        
        # --- 1. DETAY KUTUSU (ÜST KISIM) ---
        detail_box = tk.Frame(frame, bg=self.colors["light"], relief="solid", bd=2)
        
        # BURASI ÖNEMLİ: place ile tam boyut ve konum veriyoruz
        detail_box.place(relx=start_x, rely=0.1, relwidth=box_width_ratio)
        
        detail_box.grid_columnconfigure(0, weight=1)

        self.detail_title = tk.Label(detail_box, text="Toplantı Başlığı", font=self.fonts["title"], bg=self.colors["primary"], fg=self.colors["white"])
        self.detail_title.grid(row=0, column=0, sticky="ew", ipady=10)

        self.detail_time = tk.Label(detail_box, text="Zaman: 00:00", font=self.fonts["cell_main"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="w")
        self.detail_time.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Wraplength'i de daralan kutuya göre güncelledik (Kutu genişliğinin biraz altı)
        text_wrap_limit = self.content_area_width * box_width_ratio * 0.9
        
        self.detail_desc = tk.Label(detail_box, text="Açıklama...", font=self.fonts["cell_sub"], bg=self.colors["light"], fg=self.colors["text_primary"], anchor="nw", justify="left",
                                    wraplength=text_wrap_limit)
        self.detail_desc.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

        # --- 2. KATILIMCILAR ALANI (ALT KISIM) ---
        # Bunu da aynı genişlikte hemen altına koyuyoruz
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

        self.clock_label.config(text=f"⏰ {date_str} {gun_ismi}    •    {time_str}")
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
