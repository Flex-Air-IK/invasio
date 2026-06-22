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
waiting_hotkey_action = None

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
    global option_index, last_text
    condition = "\n".join(condition_texts)

    result = condition + "\n\n" + "\n".join(options)

    pyperclip.copy(result)

    print("\nFINAL RESULT:\n")
    print(result)
    print("\nCopied to clipboard!\n")

    condition_texts.clear()
    options.clear()

    option_index = 0
    last_text = ""
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
    refresh_ui()
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
main_frame = tk.Frame(root)
hotkey_frame = tk.Frame(root)
root.title("'INVASIO' - OCR Tool")
root.geometry("1000x600")

status_label = tk.Label(
    main_frame,
    text="Ready",
    font=("Arial", 30)
)
status_label.pack(pady=10)

btn_condition = tk.Button(
    main_frame,
    text="Добавить условие/Add Condition",
    width=35,
    font=("Arial", 18),
    command=gui_add_condition
)
btn_condition.pack(pady=5)

btn_option = tk.Button(
    main_frame,
    text="Добавить вариант/Add option",
    width=35,
    font=("Arial", 18),
    command=gui_add_option
)
btn_option.pack(pady=5)

btn_finish = tk.Button(
    main_frame,
    text="Собрать результат/Final Result",
    width=35,
    font=("Arial", 18),
    command=gui_finish
)
btn_finish.pack(pady=5)

btn_clear = tk.Button(
    main_frame,
    text="Очистить все/Clear Selection",
    width=35,
    font=("Arial", 18),
    command=clear_all
)
btn_clear.pack(pady=5)

preview_label = tk.Label(
    main_frame,
    text="Предпросмотр",
    font=("Arial", 15)
)
preview_label.pack(pady=(15,5))

current_screen = "main"
# =========================
# HOTKEYS
# =========================
hotkeys = {
    "condition": "F1",
    "option": "F2",
    "finish": "F3",
    "clear": "F4"
}


def set_hotkey(action, key):
    key = key.strip().upper()

    if not key:
        return

    if is_key_taken(key, ignore_action=action):
        messagebox.showwarning(
            "Кнопка уже назначена/Hotkey already used",
            f"{key} уже назначена!/{key} already assigned!"
        )
        return

    hotkeys[action] = key
    refresh_hotkey_labels()
    refresh_ui()

def create_hotkey_row(label, action):
    frame = tk.Frame(hotkey_frame)
    frame.pack(pady=5)

    tk.Label(
        frame,
        text=label,
        width=20,
        anchor="w"
    ).pack(side="left")

    key_label = tk.Label(
        frame,
        text=hotkeys[action],
        width=25
    )
    key_label.pack(side="left")

    def start_rebind():
        begin_hotkey_capture(action, key_label)

    tk.Button(
        frame,
        text="Change",
        command=start_rebind
    ).pack(side="left")

def begin_hotkey_capture(action, label_widget):
    global waiting_hotkey_action

    waiting_hotkey_action = (
        action,
        label_widget
    )
    label_widget.config(
        text="Нажми клавишу/Press a key..."
    )

# =========================
# KEY HANDLER
# =========================
def key_handler(event):
    global waiting_hotkey_action

    if waiting_hotkey_action is not None:
        action, label_widget = waiting_hotkey_action
        new_key = event.keysym

        if new_key == "Escape":
            return

        if is_key_taken(new_key, ignore_action=action):
            messagebox.showwarning(
                "Кнопка уже назначена/Button is already in use",
                f"{new_key} уже используется!/{new_key} already in use!"
            )
            waiting_hotkey_action = None
            return

        hotkeys[action] = new_key
        label_widget.config(text=new_key)

        waiting_hotkey_action = None
        refresh_hotkey_labels()
        return

    if current_screen != "main":
        return

    key = event.keysym

    if key == hotkeys["condition"]:
        gui_add_condition()
    elif key == hotkeys["option"]:
        gui_add_option()
    elif key == hotkeys["finish"]:
        gui_finish()
    elif key == hotkeys["clear"]:
        clear_all()

def is_key_taken(key, ignore_action=None):
    for action, k in hotkeys.items():
        if action != ignore_action and k == key:
            return True
    return False
# =========================
# GUI REFRESH
# =========================
def refresh_ui():
    update_preview()
    status_label.config(
        text=f"Condition fragments: {len(condition_texts)} | Options: {len(options)}"
    )
def refresh_hotkey_labels():

    btn_condition.config(
        text=f"[{hotkeys['condition']}] Добавить условие/Add Condition"
    )
    btn_option.config(
        text=f"[{hotkeys['option']}] Добавить вариант/Add Option"
    )
    btn_finish.config(
        text=f"[{hotkeys['finish']}] Собрать результат/Final Result"
    )
    btn_clear.config(
        text=f"[{hotkeys['clear']}] Очистить все/Clear Selection"
    )

refresh_hotkey_labels()
# =========================
# GUI PREVIEW WINDOW
# =========================
frame = tk.Frame(main_frame)
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

# =========================
# HOTKEY SCREEN
# =========================
def build_hotkey_screen():
    for widget in hotkey_frame.winfo_children():
        widget.destroy()
    tk.Label(hotkey_frame, text="Hotkey Settings", font=("Arial", 20)).pack(pady=10)

    create_hotkey_row("Condition", "condition")
    create_hotkey_row("Option", "option")
    create_hotkey_row("Finish", "finish")
    create_hotkey_row("Clear", "clear")

    tk.Button(hotkey_frame, text="Назад [Back]", command=show_main).pack(pady=20)

def show_main():
    global current_screen
    current_screen = "main"
    hotkey_frame.pack_forget()
    main_frame.pack(fill="both", expand=True)

def show_hotkeys():
    global current_screen
    current_screen = "hotkeys"
    main_frame.pack_forget()
    build_hotkey_screen()
    hotkey_frame.pack(fill="both", expand=True)

def on_esc(event):
    if waiting_hotkey_action is not None:
        return

    if current_screen == "hotkeys":
        show_main()

hotkey_btn = tk.Button(
    main_frame,
    text="Hotkeys",
    command=show_hotkeys
)
hotkey_btn.place(x=10, y=10)

root.bind("<Escape>", on_esc)
root.bind("<Key>", key_handler)
root.focus_set()
main_frame.pack(fill="both", expand=True)

root.mainloop()