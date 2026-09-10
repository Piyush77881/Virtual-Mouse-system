```
import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from PIL import Image, ImageTk

# Optimization and Safety
pyautogui.PAUSE = 0
# Disables the failsafe to prevent the app from crashing if your eyes snap the cursor to the absolute corner
pyautogui.FAILSAFE = False

# Initialize webcam
cam = cv2.VideoCapture(0)

# Initialize FaceMesh with explicit parameters for better stability
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
screen_w, screen_h = pyautogui.size()

# Smoothing and state variables
prev_x, prev_y = 0.0, 0.0
smoothing_factor = 0.2

# Setup Tkinter window
window = tk.Tk()
window.title("Eye Control Overlay")
window.attributes("-topmost", True)
window.overrideredirect(True)
window.geometry("+0+0")

label = tk.Label(window)
label.pack()


def update_frame() -> None:
    global prev_x, prev_y
    ret, frame = cam.read()

    # Graceful handling if the webcam drops a frame
    if not ret:
        window.after(10, update_frame)
        return

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Error handling for MediaPipe processing
    try:
        output = face_mesh.process(rgb_frame)
    except Exception as e:
        print(f"MediaPipe Error: {e}")
        window.after(10, update_frame)
        return

    landmark_points = output.multi_face_landmarks
    frame_h, frame_w, _ = frame.shape

    if landmark_points:
        landmarks = landmark_points[0].landmark

        # 1. IRIS TRACKING (Center of Eye)
        iris_pos = landmarks[468]
        eye_top = landmarks[159]
        eye_bottom = landmarks[145]

        # Cursor Movement logic
        target_x = screen_w * iris_pos.x
        target_y = screen_h * iris_pos.y
        curr_x = (target_x * smoothing_factor) + (prev_x * (1 - smoothing_factor))
        curr_y = (target_y * smoothing_factor) + (prev_y * (1 - smoothing_factor))

        # Ensure coordinates stay within monitor bounds
        curr_x = max(0, min(screen_w - 1, curr_x))
        curr_y = max(0, min(screen_h - 1, curr_y))

        pyautogui.moveTo(curr_x, curr_y)
        prev_x, prev_y = curr_x, curr_y

        # 2. EYE SCROLL LOGIC
        eye_height_total = eye_bottom.y - eye_top.y

        # Prevent ZeroDivisionError if the eye is fully closed or tracking glitches
        if eye_height_total > 0:
            iris_relative_pos = (iris_pos.y - eye_top.y) / eye_height_total

            # SCROLL UP: If iris is in the top 35% of the eye
            if iris_relative_pos < 0.35:
                pyautogui.scroll(20)

            # SCROLL DOWN: If iris is in the bottom 35% of the eye
            elif iris_relative_pos > 0.65:
                pyautogui.scroll(-20)

        # 3. CLICK LOGIC (Winks)
        left_eye_gap = landmarks[145].y - landmarks[159].y
        right_eye_gap = landmarks[374].y - landmarks[386].y

        if left_eye_gap < 0.005 and right_eye_gap > 0.005:
            pyautogui.click(button='left')
            pyautogui.sleep(0.4)
        elif right_eye_gap < 0.005 and left_eye_gap > 0.005:
            pyautogui.click(button='right')
            pyautogui.sleep(0.4)

    # UI Update (Optimized to reuse the existing rgb_frame)
    img_pil = Image.fromarray(rgb_frame)
    imgtk = ImageTk.PhotoImage(image=img_pil)
    label.imgtk = imgtk  # Keep reference to prevent garbage collection
    label.configure(image=imgtk)
    window.after(10, update_frame)


def close(event: tk.Event = None) -> None:
    cam.release()
    face_mesh.close()  # Properly release MediaPipe memory
    cv2.destroyAllWindows()
    window.destroy()


window.bind("<Escape>", close)
update_frame()
window.mainloop()
```
