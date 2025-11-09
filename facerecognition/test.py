import cv2
import numpy as np
import time
import face_recognition

# --- AYARLAR ---
CAM_LEFT_ID = 0
CAM_LEFT_WIDTH = 3264
CAM_LEFT_HEIGHT = 2448

CAM_RIGHT_ID = 2
CAM_RIGHT_WIDTH = 1280
CAM_RIGHT_HEIGHT = 720

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

COOLDOWN_SURESI = 5.0
CHECK_INTERVAL = 0.5
# -----------------

# --- KALİBRASYON VERİSİ ---
npzfile = np.load("stereo_calibration_data.npz")
mtx_l, dist_l = npzfile["mtx_l"], npzfile["dist_l"]
mtx_r, dist_r = npzfile["mtx_r"], npzfile["dist_r"]
R1, R2 = npzfile["R1"], npzfile["R2"]
P1, P2 = npzfile["P1"], npzfile["P2"]
Q = npzfile["Q"]

image_size = (TARGET_WIDTH, TARGET_HEIGHT)

map1_l, map2_l = cv2.initUndistortRectifyMap(
    mtx_l, dist_l, R1, P1, image_size, cv2.CV_16SC2
)
map1_r, map2_r = cv2.initUndistortRectifyMap(
    mtx_r, dist_r, R2, P2, image_size, cv2.CV_16SC2
)

print("Kalibrasyon verisi yüklendi ve rectification haritaları hazır.")

# --- YÜZ DEDİKTÖRÜ ---
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        raise IOError("Haar Cascade yüklenemedi")
except Exception as e:
    print(f"Hata: {e}")
    exit()

# --- KAYITLI YÜZLER ---
# known_face_encodings ve known_face_names önceden hazırlanmalı
# Örnek:
# known_face_encodings = [face_recognition.face_encodings(face_recognition.load_image_file("alice.jpg"))[0]]
# known_face_names = ["Alice"]

known_face_encodings = []  # Kendi kayıtlı yüzleri ekle
known_face_names = []

# --- KAMERALARI BAŞLAT ---
cap_left = cv2.VideoCapture(CAM_LEFT_ID)
cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_LEFT_WIDTH)
cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_LEFT_HEIGHT)
if not cap_left.isOpened():
    print(f"HATA: Sol Kamera açılamadı")
    exit()

cap_right = cv2.VideoCapture(CAM_RIGHT_ID)
cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_RIGHT_WIDTH)
cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_RIGHT_HEIGHT)
if not cap_right.isOpened():
    print(f"HATA: Sağ Kamera açılamadı")
    cap_left.release()
    exit()

print("Kameralar hazır. Yüz algılama başlatıldı. Çıkmak için 'q' tuşuna basın.")

last_capture_time = 0
last_check_time = 0

try:
    while True:
        current_time = time.time()

        if (current_time - last_check_time) > CHECK_INTERVAL:
            last_check_time = current_time

            # --- SAĞ KAMERADAN ALGILAMA ---
            ret_detect, frame_right = cap_right.read()
            if not ret_detect:
                continue

            gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_right, 1.1, 4)

            # Algılanan yüzleri göster
            for (x, y, w, h) in faces:
                cv2.rectangle(frame_right, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imshow("Sağ Kamera (Algılama)", frame_right)

            # --- YÜZ ALGILANDIYSA VE COOLDOWN TAMAMSA ---
            if len(faces) > 0 and (current_time - last_capture_time > COOLDOWN_SURESI):
                last_capture_time = current_time
                print("Yüz algılandı! Stereo çifti yakalanıyor...")

                # --- SOL VE SAĞ KAMERALARDAN KARELER ---
                ret_left, frame_left = cap_left.read()
                ret_right, frame_right = cap_right.read()
                if not ret_left or not ret_right:
                    continue

                # --- BOYUT EŞLEME ---
                frame_left_resized = cv2.resize(frame_left, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_AREA)

                # --- DÜZELTME ---
                frame_left_rect = cv2.remap(frame_left_resized, map1_l, map2_l, cv2.INTER_LINEAR)
                frame_right_rect = cv2.remap(frame_right, map1_r, map2_r, cv2.INTER_LINEAR)

                # --- KAYDET ---
                timestamp = int(time.time())
                left_filename = f"stereo_left_{timestamp}.jpg"
                right_filename = f"stereo_right_{timestamp}.jpg"
                cv2.imwrite(left_filename, frame_left_rect)
                cv2.imwrite(right_filename, frame_right_rect)
                print(f"Stereo çifti kaydedildi: {left_filename}, {right_filename}")

                # --- YÜZ ENCODING VE KİŞİ DOĞRULAMA ---
                rgb_left = cv2.cvtColor(frame_left_rect, cv2.COLOR_BGR2RGB)
                for (x, y, w, h) in faces:
                    face_img = rgb_left[y:y+h, x:x+w]
                    encodings = face_recognition.face_encodings(face_img)
                    if encodings:
                        face_encoding = encodings[0]
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                        if True in matches:
                            name = known_face_names[matches.index(True)]
                            print(f"Kayıtlı kişi bulundu: {name}")
                        else:
                            print("Yüz tanınamadı")

                # --- OPSİYONEL: Yan yana göster ---
                combined_preview = cv2.hconcat([frame_left_rect, frame_right_rect])
                cv2.imshow("Stereo Çifti (Rectified)", combined_preview)
                cv2.waitKey(1000)
                cv2.destroyWindow("Stereo Çifti (Rectified)")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    print("Kapatılıyor...")
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()