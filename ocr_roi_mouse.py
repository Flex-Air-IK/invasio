import subprocess
import cv2
import pytesseract
import pyperclip
import tkinter as tk

from tkinter import messagebox
from PIL import Image

# =========================
# STATE
# =========================
condition_texts = []
options = []
option_index = 0
mode = "condition"
last_text = ""

# =========================
# MODE HANDLING
# =========================
def switch_mode(new_mode):
    global mode
    mode = new_mode
    print(f"\n MODE: {mode}\n")

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
# CONFIG
# =========================
#Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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
# OPTIONS HANDLER (ONE BY ONE)
# =========================
def handle_option(text):
    global option_index

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return

    option_text = " ".join(lines)

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
# UPDATE THE PREVIEW IN GUI
# =========================
def update_preview():
    preview = ""

    if condition_texts:
        preview += "\n".join(condition_texts)

    if options:
        preview += "\n\n"
        preview += "\n".join(options)

    preview_text.delete("1.0", tk.END)
    preview_text.insert(tk.END, preview)

# =========================
# GUI SECTION
# =========================
def add_condition():
    switch_mode("condition")
    pipeline()

def add_option():
    switch_mode("options")
    pipeline()

def build_result():
    finish()

# =========================
# BUTTON LOGIC
# =========================
def gui_add_condition():
    switch_mode("condition")
    pipeline()
    refresh_ui()

def gui_add_option():
    switch_mode("options")
    pipeline()
    refresh_ui()

def gui_finish():
    finish()

    messagebox.showinfo(
        "Done",
        "Result copied to clipboard"
    )

def clear_all():
    global option_index, last_text

    condition_texts.clear()
    options.clear()

    option_index = 0
    last_text = ""

    status_label.config(text="Cleared")
    preview_text.delete("1.0", tk.END)
# =========================
# GUI WINDOW CONFIG
# =========================
root = tk.Tk()
root.title("'INVASIO' - OCR Tool")
root. geometry("1000x600")

status_label = tk.Label(
    root,
    text="Ready",
    font=("Arial", 30)
)
status_label.pack(pady=10)

btn_condition = tk.Button(
    root,
    text="Добавить условие [Add condition]",
    width=35,
    font=("Arial", 18),
    command=gui_add_condition
)
btn_condition.pack(pady=5)

btn_option = tk.Button(
    root,
    text="Добавить вариант [Add option]",
    width=35,
    font=("Arial", 18),
    command=gui_add_option
)
btn_option.pack(pady=5)

btn_finish = tk.Button(
    root,
    text="Собрать результат [Final Result]",
    width=35,
    font=("Arial", 18),
    command=gui_finish
)
btn_finish.pack(pady=5)

btn_clear = tk.Button(
    root,
    text="Очистить все [Clear Selection]",
    width=35,
    font=("Arial", 18),
    command=clear_all
)
btn_clear.pack(pady=5)

preview_label = tk.Label(
    root,
    text="Предпросмотр",
    font=("Arial", 15)
)
preview_label.pack(pady=(15,5))

# =========================
# GUI REFRESH
# =========================
def refresh_ui():
    update_preview()
    status_label.config(
        text=f"Condition fragments: {len(condition_texts)} | Options: {len(options)}"
    )

# =========================
# GUI PREVIEW WINDOW
# =========================
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(frame)

preview_text = tk.Text(
    frame,
    font=("Consolas", 11),
    yscrollcommand=scrollbar.set
)

scrollbar.config(command=preview_text.yview)

scrollbar.pack(side="right", fill="y")
preview_text.pack(side="left", fill="both", expand=True)

root.mainloop()