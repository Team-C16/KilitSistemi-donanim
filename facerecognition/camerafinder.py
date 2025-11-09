import cv2
import time
import numpy as np

MAX_CAMERAS_TO_CHECK = 5  # 0'dan 4'e kadar ID'leri test et

print("--- KAMERA FOTOGRAF TESTI BASLADI ---")
print("Bu kod 'while True' DONGUSU KULLANMAZ.")
print("Her kameradan SADECE BIR FOTOGRAF alip gosterecek.")
print("Lutfen sonraki kameraya gecmek icin acilan pencereye TIKLAYIP bir tusa basin.")

# Gosterilecek tum goruntuleri tutacak liste
frames_to_show = []

for i in range(MAX_CAMERAS_TO_CHECK):
    print(f"\n--- ID {i} Test Ediliyor... ---")
    
    # 1. Kamerayi acmayi dene
    cap = cv2.VideoCapture(i)
    
    if not cap.isOpened():
        print(f"ID {i}: Acilamadi veya bulunamadi.")
        continue

    # Kameranın 'ısınması' ve kareyi alması için kısa bir an bekle
    # Bazen ilk kare boş gelebilir, 2-3 kez okumak garanti olur
    ret, frame = cap.read()
    time.sleep(0.2) # Gerekirse bu süreyi 0.5 yap
    ret, frame = cap.read()

    # 2. Kamerayi HEMEN serbest birak
    print(f"ID {i}: Kamera okundu, serbest birakiliyor.")
    cap.release()

    if ret:
        print(f"ID {i}: Goruntu (fotograf) basariyla alindi.")
        
        # Görüntüye ID'sini yaz
        cv2.putText(frame, f"KAMERA ID: {i}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        frames_to_show.append((f"FOTOGRAF - ID: {i}", frame))
        
    else:
        print(f"ID {i}: Kamera acildi ama goruntu (fotograf) okunamadi.")


print("\n--- TEST TAMAMLANDI ---")

if not frames_to_show:
    print("Hicbir kameradan goruntu alinamadi.")
else:
    print(f"\nToplam {len(frames_to_show)} adet kameradan fotograf alindi.")
    print("Simdi fotograflar TEKER TEKER gosterilecek.")
    print("Pencereyi kapatip digerine gecmek icin bir tusa basin.")
    
    # 3. ALINAN TUM FOTOGRAFLARI DONGU DISINDA, TEKER TEKER GOSTER
    for (window_name, frame) in frames_to_show:
        cv2.imshow(window_name, frame)
        
        # Program burada DURUR, yeni pencere ACMAZ.
        # Siz bir tusa basana kadar bekler. (0 = sonsuza kadar bekle)
        cv2.waitKey(0) 
        
        # Tusa basinca o pencereyi kapatir
        cv2.destroyWindow(window_name)

print("Tum pencereler kapatildi. Program sonlandi.")

# Her ihtimale karsi son bir temizlik