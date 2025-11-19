import os
import sys
import time
import threading
import subprocess
import cv2

# Make sure project root (parent of this file) is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from face_blur import get_blur_function



def open_camera() -> cv2.VideoCapture:
    """Try to open a webcam and return the capture object."""
    for idx in (0, 1, 2):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"[rtsp_cam] Using camera index {idx}")
            return cap
        cap.release()
    print("[rtsp_cam] ERROR: Could not open any webcam (indices 0,1,2).", file=sys.stderr)
    sys.exit(1)


def start_vlc(rtsp_url: str) -> None:
    """Start VLC pointing at the RTSP URL."""
    print(f"[rtsp_cam] Launching VLC with {rtsp_url} ...")

    # Try VLC from PATH first
    try:
        subprocess.Popen(["vlc", rtsp_url])
        return
    except FileNotFoundError:
        pass

    # Common Windows install paths
    candidates = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    for exe in candidates:
        if os.path.exists(exe):
            subprocess.Popen([exe, rtsp_url])
            return

    print("[rtsp_cam] VLC not found; open it manually and use the RTSP URL.")


def launch_vlc_later(rtsp_url: str, delay: float = 2.0) -> None:
    """Launch VLC in a background thread after a small delay."""
    def worker():
        time.sleep(delay)
        start_vlc(rtsp_url)

    threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    ffmpeg_exe = os.environ.get("FFMPEG_EXE", "ffmpeg")
    rtsp_url = os.environ.get("RTSP_URL", "rtsp://127.0.0.1:8554/cam")

    print(f"[rtsp_cam] FFMPEG_EXE = {ffmpeg_exe}")
    print(f"[rtsp_cam] RTSP_URL   = {rtsp_url}")

    cap = open_camera()

    # ====================================== Choose blur method: 'mediapipe' or 'yolo' ===================
    # ====================================================================================================
    blur_frame = get_blur_function("mediapipe")  # change to "yolo" if you want YOLOv8

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)

    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30.0
    fps = float(fps)

    print(f"[rtsp_cam] Capture size: {width}x{height} @ {fps:.1f} fps")

    # ffmpeg reads raw frames from stdin and PUSHES them to MediaMTX
    cmd = [
        ffmpeg_exe,
        "-loglevel", "warning",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", str(int(fps)),
        "-i", "-",                # stdin from this script
        "-an",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-g", "30",
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        rtsp_url,
    ]

    print("[rtsp_cam] Starting ffmpeg:")
    print(" ".join(cmd))
    print()

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    except FileNotFoundError:
        print("[rtsp_cam] ERROR: ffmpeg executable not found. Check FFMPEG_EXE.", file=sys.stderr)
        cap.release()
        return

    print("[rtsp_cam] Streaming to RTSP server.")
    print(f"[rtsp_cam] Open this URL in VLC: {rtsp_url}")
    print()

    # ► Start VLC a bit later, in the background ◄
    launch_vlc_later(rtsp_url, delay=2.0)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[rtsp_cam] WARNING: failed to read frame, stopping.")
                break

            # Apply face blurring to the frame
            frame = blur_frame(frame)

            if proc.stdin is None:
                print("[rtsp_cam] ERROR: ffmpeg stdin is not available.")
                break

            try:
                proc.stdin.write(frame.tobytes())

            except BrokenPipeError:
                print("[rtsp_cam] ffmpeg pipe closed (BrokenPipeError).")
                break
    except KeyboardInterrupt:
        print("\n[rtsp_cam] CTRL+C received, shutting down...")
    finally:
        cap.release()
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        proc.terminate()


if __name__ == "__main__":
    main()
