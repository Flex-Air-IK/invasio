import subprocess
from PIL import Image
import pytesseract
import pyperclip
import keyboard


#Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#Cut out area
#(left top, right bottom)
ROI = (25, 160, 675, 1245)

#Phone screenshot
def make_screenshot():
    with open("screen.png", "wb") as f:
        subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            stdout=f
        )

def crop_image():
    img = Image.open("screen.png")
    cropped = img.crop(ROI)
    cropped.save("cropped.png")
    return cropped

#OCR
def ocr_and_copy(img):
    text = pytesseract.image_to_string(img, lang="eng+rus")

    pyperclip.copy(text)

    print("\n=== OCR RESULT ===")
    print(text)
    print("==================\n")

def full_pipeline():
    print("Capturing screenshot...")
    make_screenshot()

    print("Cropping area...")
    img = crop_image()

    print("Running OCR...")
    ocr_and_copy(img)

    print("Copied to clipboard!")


print("OCR HOTKEY ACTIVE")
print("Press F8 to capture phone screen")
print("Press ESC to exit")

#Hotkey
keyboard.add_hotkey("F8", full_pipeline)
#Exit
keyboard.wait("esc")