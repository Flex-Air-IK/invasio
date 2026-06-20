import subprocess
import cv2
import pytesseract
import pyperclip
import keyboard

from PIL import Image

# =========================
# CONFIG
# =========================
#Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# STATE
# =========================
condition_texts = []
options = []
options_index = 0
mode = "condition"
last_text = ""

# =========================
# PHONE SCREENSHOT
# =========================
def make_screenshot():
    with open("screen.png", "wb") as f:
        subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            stdout=f
        )
# =========================
# ROI SELECTION (SCALED)
# =========================
def select_roi_scaled(image_path, scale=0.5):
    img = cv2.imread(image_path)

    h, w = img.shape[:2]

    #Scaling down the image
    preview = cv2.resize(img, (int(w * scale), int(h * scale)))

    #User selects the area on scaled version of the image to crop
    r = cv2.selectROI("Select area (ENTER to confirm)", preview, False, False)

    cv2.destroyAllWindows()

    x,y,w_roi,h_roi = r

    #Scale back to original size
    x = int(x / scale)
    y = int(y / scale)
    w_roi = int(w_roi / scale)
    h_roi = int(h_roi / scale)

    cropped = img[y:y+h_roi, x:x+w_roi]

    cv2.imwrite("cropped.png", cropped)

    return "cropped.png"

# =========================
# TEXT CLEANING
# =========================
def clean_text(text):
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)

# =========================
# OVERLAP REMOVAL (SCROLL FIX)
# =========================
def remove_overlap (new_text, last_text):
    if not last_text:
        return new_text

    new_lines = new_text.split("\n")
    last_lines = last_text.split("\n")

    overlap = 0

    for i in range(1, min(len(new_lines), len(last_lines))+1):
        if new_lines[:i] == last_lines [-i:]:
            overlap = i
    return "\n".join(new_lines[overlap:])

# =========================
# OCR SMART CORE
# =========================
def ocr(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="eng+rus")

# =========================
# MODE HANDLING
# =========================
def switch_mode(new_mode):
    global mode, option_index
    mode = new_mode
    print(f"\n MODE: {mode}\n")
    if mode == "options":
        options.clear()
        option_index = 0
# =========================
# SMART OCR PIPELINE
# =========================

def pipeline():
    global last_text

    print(f"Screenshot in mode: {mode}")

    make_screenshot()

    cropped_path = select_roi_scaled("screen.png")

    raw_text = ocr(cropped_path)

    cleaned = clean_text(raw_text)

    processed = remove_overlap(cleaned, last_text)

    last_text = cleaned

    if mode == "condition":
        condition_texts.append(processed)
        print("CONDITION ADDED")

    elif mode == "options":
        handle_option(processed)

# =========================
# OPTIONS HANDLER (ONE BY ONE)
# =========================
def handle_option(text):
    global option_index

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return

    # берём только первый “значимый” кусок
    option_text = lines[0]

    option_index += 1

    formatted = f"{option_index}) {option_text}"

    options.append(formatted)

    print(f"OPTION {option_index} ADDED")

# =========================
# FINAL OUTPUT
# =========================

def finish():
    condition = "\n".join(condition_texts)

    result = condition + "\n\n" + "\n".join(options)

    pyperclip.copy(result)

    print("\nFINAL RESULT:\n")
    print(result)
    print("\nCopied to clipboard!\n")

    condition_texts.clear()
    options.clear()

# =========================
# HOTKEYS
# =========================

print("OCR TEST TOOL ACTIVE")
print("F7 = condition mode")
print("F8 = capture + OCR")
print("F9 = options mode (one-by-one)")
print("F10 = finish & copy")
print("ESC = exit")

keyboard.add_hotkey("F7", lambda: switch_mode("condition"))
keyboard.add_hotkey("F8", pipeline)
keyboard.add_hotkey("F9", lambda: switch_mode("options"))
keyboard.add_hotkey("F10", finish)

keyboard.wait("esc")