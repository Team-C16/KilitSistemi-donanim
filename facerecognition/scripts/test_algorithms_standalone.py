import sys
import os

# Set OpenMP fix BEFORE any CV2/Numpy imports!
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import time
import argparse

# Add parent directory to path so we can import from backend and raspberry_pi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from raspberry_pi.face_detector import FaceDetector
from backend.face_recognizer import FaceRecognizer
from backend.face_database import FaceDatabase

def test_algorithms(image_path=None, camera_index=0):
    print("="*50)
    print("  Algorithm Test: Haar Cascades + ArcFace")
    print("="*50)
    
    print("\n[1] Initializing Face Detector (Haar Cascades - CPU)...")
    detector = FaceDetector()
    
    print("[2] Initializing Face Recognizer (InsightFace ArcFace - CPU)...")
    recognizer = FaceRecognizer()

    print("[3] Loading Database...")
    db = FaceDatabase()
    
    print("Models loaded successfully!\n")

    if image_path:
        print(f"Testing on image: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            print("Error: Could not read image.")
            return
    else:
        print("Testing on webcam...")
        print(" -> Press 'e' to ENROLL the current face as 'Me'")
        print(" -> Press 'c' to CLEAR the database")
        print(" -> Press 'q' to stop.")
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return

    try:
        save_message_time = 0
        from backend.config import FACE_DB_PATH
        
        while True:
            if not image_path:
                ret, frame = cap.read()
                if not ret:
                    break
            else:
                frame = cv2.imread(image_path)

            start_det = time.time()
            faces = detector.detect(frame)
            det_time = (time.time() - start_det) * 1000

            display_frame = frame.copy()
            
            # Show "SAVED" message on screen for 2 seconds
            if time.time() - save_message_time < 2.0:
                cv2.putText(display_frame, "YOUR FACE IS SAVED!", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
            
            for i, face_data in enumerate(faces):
                face_crop = face_data["face"]
                x1, y1, x2, y2 = face_data["box"]
                conf = face_data["confidence"]
                
                # Draw detection box
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                start_rec = time.time()
                import base64
                import numpy as np
                img_bytes = base64.b64decode(face_crop) if isinstance(face_crop, str) else cv2.imencode('.jpg', face_crop)[1].tobytes()
                nparr = np.frombuffer(img_bytes, np.uint8)
                crop_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                embedding = recognizer.get_embedding(crop_img)
                rec_time = (time.time() - start_rec) * 1000

                if embedding is not None:
                    # Recognize against database
                    result = db.recognize(embedding)
                    name = result["name"]
                    score = result["score"]
                    color = (0, 255, 0) if result["matched"] else (0, 0, 255)
                    
                    cv2.putText(display_frame, f"{name} ({score:.2f})", (x1, y1-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
            # Show display and process inputs
            if not image_path:
                cv2.imshow("Algorithm Test", display_frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c'):
                    db.clear()
                elif key in [ord('e'), ord('E')]:
                    if 'embedding' in locals() and embedding is not None:
                        db.enroll("Me", [embedding])
                        save_message_time = time.time()
                        print(f"User enrolled successfully! Saved to: {os.path.abspath(FACE_DB_PATH)}")
                elif key == ord('q'):
                    break
            else:
                cv2.imshow("Algorithm Test", display_frame)
                cv2.waitKey(0)
                break

    finally:
        if not image_path:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None, help="Path to image file")
    args = parser.parse_args()
    
    test_algorithms(image_path=args.image)
