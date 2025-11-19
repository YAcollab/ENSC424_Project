# ENSC424 RTSP Webcam Demo (Windows)
This project is a one-click demo that:
1. Starts a local RTSP server (MediaMTX).
2. Captures your webcam with OpenCV in Python.
3. Sends the video to the RTSP server via FFmpeg.
4. Opens VLC to view the stream at `rtsp://127.0.0.1:8554/cam`.



# How to run (Windows)
1. **Requirements (first run)**
   - Windows 10/11  
   - Internet connection  
   - `winget` available (if not, install **“App Installer”** from the Microsoft Store)  
   - A webcam

2. **Start the demo**
   - In File Explorer, open the project folder (the one that contains `scripts` and `rtsp-stream`).
   - Double-click:  
     `scripts\run_windows.bat`

3. **What happens on first run**
   - The script checks/installs:
     - Python (via `winget`)
     - FFmpeg (via `winget`)
     - VLC (via `winget`)
   - It creates a virtual environment in `.venv` (if not already there).
   - It installs Python packages inside `.venv` (OpenCV, NumPy).
   - It starts **MediaMTX** (`mediamtx.exe`) using `mediamtx.yml`.
   - It runs `rtsp-stream/rtsp_cam.py`, which opens the webcam and starts streaming.

4. **Viewing the video**
   - Your **webcam light should turn on** once streaming starts.
   - A couple of seconds later **VLC should launch automatically** and connect to:  
     `rtsp://127.0.0.1:8554/cam`
   - If VLC does **not** open automatically:
     1. Open VLC manually.
     2. Go to **Media → Open Network Stream…**
     3. Enter `rtsp://127.0.0.1:8554/cam` and click **Play**.

5. **Stopping everything**
   - Close the Python/terminal window (or press `Ctrl+C` in it).
   - The script will stop MediaMTX and then exit.

> **Firewall note:** the first time you run this, Windows Firewall may ask about `python.exe`, `mediamtx.exe` or `vlc.exe`. Allow them on **Private networks** so the local RTSP connection works.



# Project structure
# `.venv/`
- Python virtual environment created automatically by the launcher.
- Contains all Python dependencies used by the demo (e.g., `opencv-python`, `numpy`).
- You normally **don’t need to edit anything here**.

# `rtsp-stream/`
- **`rtsp_cam.py`**  
  - Python script that:
    - Opens the first available webcam using OpenCV.
    - Sends frames to FFmpeg via stdin.
    - FFmpeg encodes the frames (H.264) and pushes them to the RTSP server at `rtsp://127.0.0.1:8554/cam`.
    - After streaming starts, it launches VLC (after a short delay) so you see the video automatically.

- **`mediamtx.exe`**  
  - MediaMTX RTSP server binary for Windows.
  - Listens on port **8554** for RTSP and hosts the `/cam` stream.

- **`mediamtx.yml`**  
  - Configuration file for MediaMTX.
  - Defines the RTSP ports, protocols, and the `cam` path used by this demo.

- **`LICENSE`**  
  - License file for MediaMTX.

# `scripts/`
- **`run_windows.bat`**  
  - Simple batch file you double-click.
  - Calls `run_windows_any.ps1` with PowerShell.

- **`run_windows_any.ps1`**  
  - Main launcher/orchestration script. It:
    - Locates the project root.
    - Creates/activates the `.venv` virtual environment.
    - Installs required Python packages inside `.venv`.
    - Ensures Python, FFmpeg and VLC are installed (via `winget`).
    - Sets environment variables:
      - `FFMPEG_EXE` — path to the ffmpeg executable.
      - `RTSP_URL` — `rtsp://127.0.0.1:8554/cam`.
    - Starts `mediamtx.exe` with `mediamtx.yml`.
    - Runs `rtsp_cam.py` (which starts streaming and then launches VLC).
    - Shuts down MediaMTX when the Python script exits.



# `README.md`