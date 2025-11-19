import cv2

# Load Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Mode: 'blur' or 'pixel'
mode = "blur"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # --------- SPEED BOOST: Resize frame for faster detection ---------
    scale_factor = 0.5  # detect on a 50% smaller image
    small = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)

    # Convert small frame to grayscale
    gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # Detect faces on the smaller frame
    faces_small = face_cascade.detectMultiScale(
        gray_small,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # --------- SCALE COORDINATES BACK TO FULL SIZE ---------
    faces = []
    for (x, y, w, h) in faces_small:
        faces.append((
            int(x / scale_factor),
            int(y / scale_factor),
            int(w / scale_factor),
            int(h / scale_factor)
        ))

    # --------- APPLY BLUR OR PIXELATION ---------
    for (x, y, w, h) in faces:
        face = frame[y:y+h, x:x+w]

        if mode == "blur":
            # Strong Gaussian blur
            blurred = cv2.GaussianBlur(face, (51, 51), 30)
            frame[y:y+h, x:x+w] = blurred

        elif mode == "pixel":
            # Pixelation: shrink → expand
            small_face = cv2.resize(face, (16, 16), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small_face, (w, h), interpolation=cv2.INTER_NEAREST)
            frame[y:y+h, x:x+w] = pixelated

    # Show output
    cv2.imshow("Webcam Face Blur / Pixelation", frame)

    # Key controls
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    if key == ord('p'):
        mode = "pixel"
        print("Mode: Pixelation")
    if key == ord('b'):
        mode = "blur"
        print("Mode: Blur")

cap.release()
cv2.destroyAllWindows()
