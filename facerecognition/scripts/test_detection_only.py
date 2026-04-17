import sys
import os
import cv2
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from raspberry_pi.face_detector import FaceDetector

def test_detection():
    print("="*50)
    print("  TEST 1: Edge Detection Algorithm (Haar Cascades)")
    print("="*50)
    
    print("Initializing...")
    detector = FaceDetector()
    cap = cv2.VideoCapture(0)
    
    print("\nStarting webcam... Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        start = time.time()
        faces = detector.detect(frame)
        det_time = (time.time() - start) * 1000
        
        display = frame.copy()
        for face in faces:
            x1, y1, x2, y2 = face["box"]
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display, f"Haar Detect: {det_time:.1f}ms", (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        cv2.imshow("Detection Test", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_detection()
