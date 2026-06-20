import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#OCR
img = Image.open("C:\\Users\Jake\PycharmProjects\OCR\ocr_screens\screen.png")
text = pytesseract.image_to_string(img,lang="eng+rus")
text = text.strip()

print(text)