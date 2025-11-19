import cv2
import numpy as np

# Global YOLO model instance (so we only load it once)
_model = None


def _get_model():
    """Lazily load the YOLOv8 face model once and reuse it."""
    global _model
    if _model is None:
        try:
            # Import here so MediaPipe-only setups don't require ultralytics
            from ultralytics import YOLO

            # ultralytics will download yolov8n_100e.pt the first time if needed
            _model = YOLO("yolov8n_100e.pt")
        except Exception as e:
            print(f"Error loading YOLOv8-face model: {e}")
            print("Please ensure the weights file is available or you have internet access.")
            raise
    return _model


def blur_face(frame, box):
    """Apply Gaussian blur to a single detected face region.

    Args:
        frame: The full BGR image.
        box:   Bounding box (tensor or array-like) with [x1, y1, x2, y2].
    """
    x1, y1, x2, y2 = map(int, box)

    # Clamp to frame boundaries
    h, w = frame.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return frame

    face_roi = frame[y1:y2, x1:x2]

    if face_roi.size == 0:
        return frame

    # Apply Gaussian blur (51x51 kernel is quite strong)
    blurred_face = cv2.GaussianBlur(face_roi, (51, 51), 0)

    # Put blurred patch back
    frame[y1:y2, x1:x2] = blurred_face
    return frame


def blur_frame(frame):
    """Detect faces in a BGR frame with YOLOv8 and blur them."""
    model = _get_model()

    results = model(frame, stream=True)
    for r in results:
        for box in r.boxes:
            frame = blur_face(frame, box.xyxy[0])

    return frame


def main():
    """Standalone test: blur faces from your webcam using YOLOv8."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Webcam started. Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            break

        frame = blur_frame(frame)

        cv2.imshow("Webcam - Face Blurring with YOLOv8", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
