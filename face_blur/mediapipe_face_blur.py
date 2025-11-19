import cv2
import mediapipe as mp

# MediaPipe face detection module
mp_face_detection = mp.solutions.face_detection

# Keep a single detector instance so it's fast when called from a loop
_face_detector = None


def _get_detector():
    global _face_detector
    if _face_detector is None:
        _face_detector = mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.6,
        )
    return _face_detector


def blur_frame(frame):
    """Detect faces in a BGR frame and blur them. Returns the modified frame."""
    detector = _get_detector()

    # MediaPipe expects RGB input
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb_frame)

    if not results.detections:
        return frame

    h, w, _ = frame.shape

    for detection in results.detections:
        bbox = detection.location_data.relative_bounding_box

        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        w_box = int(bbox.width * w)
        h_box = int(bbox.height * h)

        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        x2 = min(w, x + max(0, w_box))
        y2 = min(h, y + max(0, h_box))

        if x2 <= x or y2 <= y:
            continue

        face_roi = frame[y:y2, x:x2]
        if face_roi.size == 0:
            continue

        blurred_face = cv2.GaussianBlur(face_roi, (55, 55), 30)
        frame[y:y2, x:x2] = blurred_face

    return frame


def main():
    """Standalone test: blur faces from your webcam using MediaPipe."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("MediaPipe blur demo. Press ESC to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = blur_frame(frame)
        cv2.imshow("MediaPipe Face Blur (debug)", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
