"""
Test Recognition Script - Test the face recognition pipeline.

Opens webcam, detects faces, sends them to backend, and displays results.
Useful for verifying the system works before deploying to Raspberry Pi.

Usage:
    python test_recognition.py
    python test_recognition.py --server http://192.168.1.100:8000
    python test_recognition.py --image path/to/face.jpg
"""

import cv2
import sys
import argparse
import requests
import time
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Test face recognition")
    parser.add_argument("--server", default="http://localhost:8000", help="Backend server URL")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--image", type=str, default=None, help="Test with a single image file")
    return parser.parse_args()


def test_with_image(image_path, server_url):
    """Test recognition with a single image file."""
    print(f"\nTesting with image: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Cannot read image: {image_path}")
        sys.exit(1)

    _, buffer = cv2.imencode(".jpg", img)
    files = {"image": ("test.jpg", buffer.tobytes(), "image/jpeg")}

    try:
        response = requests.post(f"{server_url}/recognize", files=files, timeout=10)
        result = response.json()

        print(f"\n  Result:")
        print(f"    Name:    {result.get('name', 'N/A')}")
        print(f"    Score:   {result.get('score', 0):.4f}")
        print(f"    Matched: {result.get('matched', False)}")

    except Exception as e:
        print(f"\nERROR: {e}")


def test_with_camera(camera_index, server_url):
    """Test recognition with live webcam feed."""
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  Face Recognition Test")
    print(f"  Server: {server_url}")
    print(f"{'='*50}")
    print(f"\n  SPACE = Recognize | Q = Quit\n")

    # Check server connection
    try:
        r = requests.get(f"{server_url}/", timeout=5)
        info = r.json()
        print(f"  Server status: {info.get('status', 'unknown')}")
        print(f"  Enrolled people: {info.get('enrolled_people', 0)}\n")
    except Exception:
        print("  WARNING: Cannot reach server. Make sure backend is running.\n")

    last_result = None
    auto_mode = False

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        display = frame.copy()
        h, w = display.shape[:2]

        # Draw header
        cv2.rectangle(display, (0, 0), (w, 40), (0, 0, 0), -1)
        mode_text = "AUTO" if auto_mode else "MANUAL (SPACE to recognize)"
        cv2.putText(
            display, f"Mode: {mode_text}",
            (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
        )

        # Draw last result
        if last_result:
            name = last_result.get("name", "unknown")
            score = last_result.get("score", 0)
            matched = last_result.get("matched", False)

            color = (0, 255, 0) if matched else (0, 0, 255)
            text = f"{name} ({score:.3f})" if matched else f"Unknown ({score:.3f})"

            cv2.rectangle(display, (0, h - 50), (w, h), (0, 0, 0), -1)
            cv2.putText(
                display, text,
                (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2,
            )

        cv2.imshow("Recognition Test", display)

        key = cv2.waitKey(1) & 0xFF

        # Toggle auto mode with 'A'
        if key == ord("a"):
            auto_mode = not auto_mode
            print(f"  Auto mode: {'ON' if auto_mode else 'OFF'}")

        # Recognize on SPACE or in auto mode
        should_recognize = (key == ord(" ")) or auto_mode

        if should_recognize:
            _, buffer = cv2.imencode(".jpg", frame)
            files = {"image": ("test.jpg", buffer.tobytes(), "image/jpeg")}

            try:
                response = requests.post(
                    f"{server_url}/recognize",
                    files=files,
                    timeout=5,
                )
                last_result = response.json()
                name = last_result.get("name", "unknown")
                score = last_result.get("score", 0)
                print(f"  → {name} (score: {score:.4f})")

            except Exception as e:
                print(f"  Error: {e}")

            if auto_mode:
                time.sleep(1)  # Rate limit in auto mode

        elif key == ord("q") or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    args = parse_args()

    if args.image:
        test_with_image(args.image, args.server)
    else:
        test_with_camera(args.camera, args.server)
