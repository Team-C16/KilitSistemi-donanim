import sys
import os
import cv2
import time
import numpy as np

# Windows OpenMP fix MUST be at the very top
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Import Uniface for Anti-Spoofing
from uniface.spoofing import MiniFASNet

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.face_recognizer import FaceRecognizer
from backend.face_database import FaceDatabase
from backend.audit_logger import AuditLogger

def test_recognition():
    print("="*50)
    print("  TEST 2: Backend Recognition Algorithm (InsightFace + Liveness)")
    print("="*50)
    
    print("Initializing heavy InsightFace AI... (Takes ~10 seconds)")
    recognizer = FaceRecognizer()
    
    print("Initializing Database...")
    face_db = FaceDatabase()
    
    print("Initializing Audit Logger...")
    audit_log = AuditLogger()
    
    print("Initializing Anti-Spoofing Liveness AI (MiniFASNet)...")
    spoofer = MiniFASNet()
    
    cap = cv2.VideoCapture(0)
    
    print("\nStarting webcam...")
    print(" -> Real-time recognition using vectors in backend/data/face_db.json.")
    print(" -> Press 'e' to ENROLL current face to database (Fake/Test User).")
    print(" -> Press 'c' to CLEAR the entire database.")
    print(" -> Press 'q' to quit.")
    
    consecutive_real_frames = 0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        start = time.time()
        # We access recognizer.app directly to get the RAW insightface objects so we can use eyelids/landmarks!
        faces = recognizer.app.get(frame)
        rec_time = (time.time() - start) * 1000
        
        display = frame.copy()
        
        # Check keys after imshow processes
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        # --- SECURITY RULE 4: THE "GHOST BLINK" FIX ---
        # If the person leaves the frame, completely wipe the memory.
        # Otherwise, a hacker could shove a photo in right after a real person steps away!
        if len(faces) == 0:
            consecutive_real_frames = 0
            if hasattr(sys, '_has_blinked'): sys._has_blinked = False
            if hasattr(sys, '_blink_state'): sys._blink_state = False
            
        # --- SECURITY RULE 5: ANTI-TAILGATING (MULTI-FACE LOCKDOWN) ---
        # For a high-security door, we ONLY allow one person in the frame at a time.
        # If someone is hiding behind a teacher, or holding a photo next to their face, lock the system!
        is_multi_face_lockdown = len(faces) > 1
            
        for face in faces:
            x1, y1, x2, y2 = map(int, face.bbox)
            emb = face.embedding / np.linalg.norm(face.embedding) # Normalize it exactly like the wrapper does
            bbox = face.bbox
            
            # ---- LIVENESS DETECTION ----
            liveness_start = time.time()
            spoof_result = spoofer.predict(frame, bbox)
            liveness_time = (time.time() - liveness_start) * 1000
            
            is_real = spoof_result.is_real
            liveness_conf = spoof_result.confidence
            
            # --- SECURITY RULE 1: PROXIMITY BLOCK ---
            frame_h, frame_w = frame.shape[:2]
            face_h = y2 - y1
            face_height_ratio = face_h / frame_h
            too_close = face_height_ratio > 0.45 # If face takes >45% of the vertical screen height
            
            # --- STRICT LIVENESS OVERRIDE ---
            STRICT_THRESHOLD = 0.90
            if is_real and (liveness_conf < STRICT_THRESHOLD or too_close):
                is_real = False # Force it to fail!
                
            # Provide nuke logic for failed states, "too close", or MULTI-FACE LOCKDOWN
            if too_close or (is_real == False) or is_multi_face_lockdown:
                consecutive_real_frames = 0
                is_real = False
                
            # --- SECURITY RULE 2: TEMPORAL CONSISTENCY ---
            if is_real and not is_multi_face_lockdown:
                consecutive_real_frames += 1
            else:
                consecutive_real_frames = 0
                
            is_fully_validated = consecutive_real_frames >= 5
            
            # --- HOTKEY ACTIONS ---
            if key == ord('e') or key == ord('E'):
                if is_multi_face_lockdown:
                    print("❌ Cannot enroll: Multiple faces detected!")
                elif is_fully_validated:
                    # Check if person already exists to prevent duplicate enrollment
                    match = face_db.recognize(emb)
                    if match["matched"]:
                        print(f"❌ Cannot enroll: Person already exists as '{match['name']}' (Sim: {match['score']:.2f})!")
                    else:
                        user_name = f"TestUser_{int(time.time())}"
                        face_db.enroll(user_name, [emb])
                        print(f"✅ Enrolled {user_name} into database!")
                else:
                    print("❌ Face must be fully validated (hold still) before enrolling!")

            if key == ord('c') or key == ord('C'):
                face_db.clear()
                print("✅ Database cleared!")
            
            # Default Box Color
            box_color = (255, 0, 0)
            
            # Use FaceDatabase vector search!
            match_result = face_db.recognize(emb)
            if match_result["matched"]:
                box_color = (0, 255, 0)
                label_identity = f"{match_result['name']} ({match_result['score']:.2f})"
                
                # --- AUDIT LOGGING (SUCCESS) ---
                # Only log exactly on the 5th verified frame to prevent spamming the database 30 times a second
                if consecutive_real_frames == 5:
                    audit_log.log_event("DOOR_UNLOCK_SUCCESS", match_result['name'], match_result['score'], "Person passed liveness and matched")
                     # Print to terminal using cyan color
                    print(f"\033[96m📄 AUDIT LOG:\033[0m Door unlocked for '{match_result['name']}' at {time.strftime('%H:%M:%S')}")
                    
            else:
                box_color = (0, 0, 255)
                label_identity = f"UNKNOWN ({match_result['score']:.2f})"
                
                # --- AUDIT LOGGING (FAILED) ---
                if consecutive_real_frames == 5:
                    audit_log.log_event("DOOR_UNLOCK_FAILED", "UNKNOWN", match_result['score'], "Person passed liveness but no database match")
                    print(f"\033[91m📄 AUDIT LOG:\033[0m Unknown person attempted unlock at {time.strftime('%H:%M:%S')}")
                    
            if not is_fully_validated:
                label_identity = "LIVENESS FAILED"
                
            if is_multi_face_lockdown:
                label_identity = "LOCKDOWN"
                
            # Add realtime Yaw diagnostics
            if hasattr(sys, '_current_yaw'):
                label_identity += f" (Yaw: {sys._current_yaw:.1f} deg)"
            
            # 2. Second line: Liveness
            current_state = getattr(sys, '_liveness_state', 'WAITING_LEFT')
            
            if is_multi_face_lockdown:
                label_liveness = "ANTI-TAILGATE: ONE PERSON ONLY!"
                box_color = (0, 0, 255) # Red
            elif is_fully_validated:
                label_liveness = f"REAL ({liveness_conf:.2f})"
            elif too_close:
                label_liveness = "MOVE FURTHER AWAY!"
                box_color = (0, 0, 255) # Red
            elif current_state == 'WAITING_LEFT':
                label_liveness = "CHALLENGE: TURN HEAD LEFT!"
                box_color = (0, 165, 255) # Orange
            elif current_state == 'WAITING_RIGHT':
                label_liveness = "CHALLENGE: TURN HEAD RIGHT!"
                box_color = (0, 165, 255) # Orange
            elif is_real and not is_fully_validated:
                label_liveness = f"HOLD STILL... ({consecutive_real_frames}/5)"
                box_color = (0, 165, 255) # Orange
            else:
                label_liveness = f"SPOOF/FAKE ({liveness_conf:.2f})"
                box_color = (0, 0, 255) # Red
                
            # Draw box and text
            cv2.rectangle(display, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(display, label_identity, (x1, y1-25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            cv2.putText(display, label_liveness, (x1, y1-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
        
        cv2.putText(display, f"DB Loaded: {len(face_db.db.get('people', {}))} people vectors", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
        cv2.imshow("Recognition Extractor Test", display)
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_recognition()
