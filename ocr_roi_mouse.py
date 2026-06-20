import subprocess
import cv2
import pytesseract
import pyperclip
import keyboard

from PIL import Image

session_texts = []
last_text = ""

#Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#Phone screenshot
def make_screenshot():
    with open("screen.png", "wb") as f:
        subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            stdout=f
        )

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

def ocr_and_store(image_path):
    global last_text

    img = Image.open(image_path)

    raw_text = pytesseract.image_to_string(img, lang="eng+rus")

    cleaned = clean_text(raw_text)
    processed = remove_overlap(cleaned, last_text)
    last_text = cleaned


    session_texts.append(processed)

    print("\n=== OCR RESULT ===")
    print(processed)
    print("==================\n")

#Cleans spaces and empty lines
def clean_text(text):
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    return "\n".join(lines)

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

def pipeline():
    print("Capturing screenshot...")
    make_screenshot()

    print("Select area with mouse...")
    cropped_path = select_roi_scaled("screen.png")

    print("OCR...")

    ocr_and_store(cropped_path)

    print("Copied to clipboard!")

def finish_session():
    full_text = "\n".join(session_texts)

    #Final cleanup
    lines = [line.strip() for line in full_text.split("\n")]
    lines = [line for line in lines if line]

    final_text = "\n".join(lines)

    pyperclip.copy(final_text)

    print("\n SMART FINAL DOCUMENT:\n")
    print(final_text)
    print("\nCopied to clipboard!")

print("OCR HOTKEY ACTIVE")
print("Press F8 to capture phone screen")
print("Press ESC to exit")

#Hotkeys
keyboard.add_hotkey("F8", pipeline)
keyboard.add_hotkey("F9", finish_session)
#Exit
keyboard.wait("esc")