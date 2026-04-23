"""
Main entry point for Raspberry Pi face detection.

Pipeline:
1. Capture frame from camera
2. Detect faces using OpenCV DNN (CPU)
3. Send cropped face(s) to backend for recognition
4. Display results (optional, for debugging)

Usage:
    python main.py                  # WebSocket mode (default)
    python main.py --http           # HTTP fallback mode
    python main.py --display        # Show video feed with detections
    python main.py --http --display # HTTP mode with display
"""

import cv2
import sys
import time
import asyncio
import argparse
from camera import Camera
from face_detector import FaceDetector
from sender import WebSocketSender, HTTPSender
from config import SEND_INTERVAL


def parse_args():
    parser = argparse.ArgumentParser(description="Raspberry Pi Face Detection")
    parser.add_argument(
        "--http", action="store_true",
        help="Use HTTP instead of WebSocket for backend communication"
    )
    parser.add_argument(
        "--display", action="store_true",
        help="Show video feed with detection overlays (requires display)"
    )
    return parser.parse_args()


async def run_websocket_mode(display=False):
    """Main loop using WebSocket for real-time communication."""
    camera = Camera()
    detector = FaceDetector()
    sender = WebSocketSender()

    await sender.connect()

    last_send_time = 0
    frame_count = 0
    fps_start = time.time()

    print("\n[Main] Starting face detection loop (WebSocket mode)")
    print("[Main] Press Ctrl+C to stop\n")

    try:
        while True:
            frame = camera.read()
            if frame is None:
                continue

            # Detect faces
            faces = detector.detect(frame)
            frame_count += 1
            frame_h = frame.shape[0]  # Frame height for proximity rule

            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = frame_count / elapsed
                print(f"[Main] FPS: {fps:.1f} | Faces detected: {len(faces)}")

            current_time = time.time()

            # ── RULE 4: Ghost Blink Fix ─────────────────────────────────────
            # When no face is in frame, notify backend to reset its counter.
            if not faces and (current_time - last_send_time) >= SEND_INTERVAL:
                await sender.send_no_face()
                last_send_time = current_time

            # Send faces to backend (rate-limited)
            elif faces and (current_time - last_send_time) >= SEND_INTERVAL:
                face_count = len(faces)  # Total faces for anti-tailgating rule
                for face_data in faces:
                    result = await sender.send_face(
                        face_data["face"],
                        face_data["box"],
                        face_data["confidence"],
                        frame_h,
                        face_count,
                    )

                    if result:
                        name  = result.get("name", "unknown")
                        score = result.get("score", 0)
                        label = result.get("label", "")
                        validated = result.get("is_validated", False)
                        print(f"  → {label} | {name} (score: {score:.3f}) | validated: {validated}")

                last_send_time = current_time

            # Display frame (optional)
            if display:
                display_frame = detector.draw_detections(frame, faces)
                cv2.imshow("Face Detection", display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Small sleep to prevent CPU hogging
            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[Main] Stopping...")
    finally:
        await sender.close()
        camera.release()
        if display:
            cv2.destroyAllWindows()


def run_http_mode(display=False):
    """Main loop using HTTP for backend communication."""
    camera = Camera()
    detector = FaceDetector()
    sender = HTTPSender()

    last_send_time = 0
    frame_count = 0
    fps_start = time.time()

    print("\n[Main] Starting face detection loop (HTTP mode)")
    print("[Main] Press Ctrl+C to stop\n")

    try:
        while True:
            frame = camera.read()
            if frame is None:
                continue

            # Detect faces
            faces = detector.detect(frame)
            frame_count += 1

            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = frame_count / elapsed
                print(f"[Main] FPS: {fps:.1f} | Faces detected: {len(faces)}")

            current_time = time.time()

            # Send faces to backend (rate-limited)
            if faces and (current_time - last_send_time) >= SEND_INTERVAL:
                for face_data in faces:
                    result = sender.send_face(
                        face_data["face"],
                        face_data["box"],
                        face_data["confidence"],
                    )

                    if result:
                        name = result.get("name", "unknown")
                        score = result.get("score", 0)
                        print(f"  → Recognized: {name} (score: {score:.3f})")

                last_send_time = current_time

            # Display frame (optional)
            if display:
                display_frame = detector.draw_detections(frame, faces)
                cv2.imshow("Face Detection", display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Small sleep to prevent CPU hogging
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[Main] Stopping...")
    finally:
        sender.close()
        camera.release()
        if display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    args = parse_args()

    if args.http:
        run_http_mode(display=args.display)
    else:
        asyncio.run(run_websocket_mode(display=args.display))
