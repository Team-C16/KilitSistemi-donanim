import cv2
import numpy as np
import time

# --- AYNI AYARLAR test.py'den ---
CAM_LEFT_ID = 0
CAM_LEFT_WIDTH = 3264
CAM_LEFT_HEIGHT = 2448
CAM_RIGHT_ID = 2
CAM_RIGHT_WIDTH = 1280
CAM_RIGHT_HEIGHT = 720
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
# --------------------------------

# --- SATRANÇ TAHTASI AYARLARI ---
chessboard_width = 9
chessboard_height = 6
# --------------------------------

print("Kalibrasyon Script'i Başladı.")
print("Görüntü almak için 'c' tuşuna basın.")
print("Kalibrasyonu tamamlamak için 'q' tuşuna basın.")

# 3D noktalar
objp = np.zeros((chessboard_height * chessboard_width, 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_width, 0:chessboard_height].T.reshape(-1, 2)

objpoints = []
imgpoints_left = []
imgpoints_right = []

# Kameraları başlat
cap_left = cv2.VideoCapture(CAM_LEFT_ID)
cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_LEFT_WIDTH)
cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_LEFT_HEIGHT)

cap_right = cv2.VideoCapture(CAM_RIGHT_ID)
cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_RIGHT_WIDTH)
cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_RIGHT_HEIGHT)

if not cap_left.isOpened() or not cap_right.isOpened():
    print("HATA: Kameralar açılamadı.")
    exit()

cv2.namedWindow("Stereo Kalibrasyon", cv2.WINDOW_NORMAL)  # sadece bir kez oluştur
cv2.resizeWindow("Stereo Kalibrasyon", TARGET_WIDTH * 2, TARGET_HEIGHT)

print("Kameralar hazır. Lütfen satranç tahtasını gösterin.")
img_counter = 0

try:
    while True:
        ret_left, frame_left_highres = cap_left.read()
        ret_right, frame_right_lowres = cap_right.read()

        if not ret_left or not ret_right:
            print("HATA: Kare okunamadı.")
            continue

        # Sol kamerayı küçült
        frame_left_resized = cv2.resize(frame_left_highres, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_AREA)

        preview_left = frame_left_resized.copy()
        preview_right = frame_right_lowres.copy()

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Kalibrasyondan çıkılıyor...")
            break

        elif key == ord('c'):
            print(f"Görüntü {img_counter} yakalanıyor... Köşeler aranıyor...")

            gray_left = cv2.cvtColor(frame_left_resized, cv2.COLOR_BGR2GRAY)
            gray_right = cv2.cvtColor(frame_right_lowres, cv2.COLOR_BGR2GRAY)

            ret_l, corners_l = cv2.findChessboardCorners(gray_left, (chessboard_width, chessboard_height), None)
            ret_r, corners_r = cv2.findChessboardCorners(gray_right, (chessboard_width, chessboard_height), None)

            if ret_l and ret_r:
                img_counter += 1
                print(f"BAŞARILI: Her iki görüntüde de köşeler bulundu. (Toplam: {img_counter})")

                objpoints.append(objp)
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

                corners_l_refined = cv2.cornerSubPix(gray_left, corners_l, (11, 11), (-1, -1), criteria)
                imgpoints_left.append(corners_l_refined)

                corners_r_refined = cv2.cornerSubPix(gray_right, corners_r, (11, 11), (-1, -1), criteria)
                imgpoints_right.append(corners_r_refined)

                cv2.drawChessboardCorners(preview_left, (chessboard_width, chessboard_height), corners_l_refined, ret_l)
                cv2.drawChessboardCorners(preview_right, (chessboard_width, chessboard_height), corners_r_refined, ret_r)
                print("Köşeler çizildi, 1 saniye bekleyin...")
                time.sleep(1)
            else:
                print("UYARI: Köşeler her iki görüntüde de bulunamadı. Lütfen tekrar deneyin.")

        # --- PENCERE TEK, SADECE GÜNCELLENİYOR ---
        preview_combined = cv2.hconcat([preview_left, preview_right])
        cv2.imshow("Stereo Kalibrasyon", preview_combined)
        # ------------------------------------------

except Exception as e:
    print(f"Bir hata oluştu: {e}")

finally:
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

# --- KALİBRASYON HESAPLAMA ---
if len(objpoints) > 10:
    print("\nYeterli görüntü toplandı. Stereo kalibrasyon hesaplanıyor...")
    gray_shape = (TARGET_HEIGHT, TARGET_WIDTH)

    ret_l, mtx_l, dist_l, rvecs_l, tvecs_l = cv2.calibrateCamera(objpoints, imgpoints_left, gray_shape, None, None)
    ret_r, mtx_r, dist_r, rvecs_r, tvecs_r = cv2.calibrateCamera(objpoints, imgpoints_right, gray_shape, None, None)

    print("Bireysel kalibrasyonlar tamamlandı. Stereo kalibrasyon (dışsal) başlıyor...")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    ret, mtx_l, dist_l, mtx_r, dist_r, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right,
        mtx_l, dist_l, mtx_r, dist_r, gray_shape,
        criteria=criteria, flags=cv2.CALIB_FIX_INTRINSIC
    )

    if ret:
        print("\nKALİBRASYON BAŞARILI!")
        R1, R2, P1, P2, Q, roi_l, roi_r = cv2.stereoRectify(
            mtx_l, dist_l, mtx_r, dist_r, gray_shape, R, T, alpha=0.9
        )

        np.savez("stereo_calibration_data.npz",
                 mtx_l=mtx_l, dist_l=dist_l,
                 mtx_r=mtx_r, dist_r=dist_r,
                 R=R, T=T, E=E, F=F,
                 R1=R1, R2=R2, P1=P1, P2=P2, Q=Q,
                 roi_l=roi_l, roi_r=roi_r)
        print("Kaydedildi. Artık derinlik haritası oluşturabilirsiniz.")
    else:
        print("\nKALİBRASYON BAŞARISIZ OLDU.")
else:
    print(f"\nKalibrasyon için yetersiz görüntü ({len(objpoints)}) — en az 10 gerekli.")