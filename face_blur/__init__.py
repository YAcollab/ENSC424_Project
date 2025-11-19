from .mediapipe_face_blur import blur_frame as mediapipe_blur_frame
from .yolov8_face_blur import blur_frame as yolo_blur_frame


def get_blur_function(method: str):
    """Return a function blur_frame(frame) for the chosen method.

    method: "mediapipe" or "yolo"
    """
    method = method.lower().strip()
    if method == "mediapipe":
        return mediapipe_blur_frame
    elif method == "yolo":
        return yolo_blur_frame
    else:
        raise ValueError(f"Unknown blur method: {method}")
