import pytesseract
from PIL import Image
import pyperclip
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#Phone Screenshot
os.system("adb exec-out screencap -p > screen.png")
#OCR
img = Image.open("screen.png")
text = pytesseract.image_to_string(img,lang="eng+rus")
text = text.strip()
#clipboard
pyperclip.copy(text)
#Output
print("===OUTPUT===")
print(text)
print("============")