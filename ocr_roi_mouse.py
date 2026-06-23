import subprocess
import cv2
import pytesseract
import pyperclip
import tkinter as tk
import json
import webbrowser
import os

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
# THEME
# =========================
BG = "#1e1e1e"          # фон окна
CARD = "#2d2d2d"        # карточки/панели
BTN = "#3a3a3a"         # кнопки
BTN_HOVER = "#505050"   # кнопки при наведении
TEXT = "#ffffff"        # белый текст
ACCENT = "#4CAF50"      # зеленый акцент
PREVIEW_BG = "#252526"  # фон preview
PREVIEW_TEXT = "#d4d4d4"

# =========================
# MODE HANDLING
# =========================
def switch_mode(new_mode):
    global mode
    mode = new_mode
    print(f"\n MODE: {mode}\n")

# =========================
# RESOURCES
# =========================
TELEGRAM_URL = "https://t.me/IK_Flex_Air"
YOUTUBE_URL = "https://www.youtube.com/@FlexAir-pwn"

def open_link(url):
    webbrowser.open(url)

def copy_link(url):
    pyperclip.copy(url)

    messagebox.showinfo(
        "Copied",
        "Link copied to clipboard"
    )
def copy_text(text):
    pyperclip.copy(text)
    messagebox.showinfo("Copied", "Address copied to clipboard")

def copy_address(address, widget):
    pyperclip.copy(address)
    widget.tooltip_label.config(
        text="Copied!"
    )

    widget.after(
        1500,
        lambda: widget.tooltip_label.config(
            text="Copy to clipboard"
        )
    )

# =========================
# Tooltip
# =========================
def show_tooltip(event, text):

    widget = event.widget

    widget.tooltip_label = tk.Label(
        root,
        text=text,
        bg="#ffffe0",
        relief="solid",
        borderwidth=1,
        font=("Arial", 9)
    )

    widget.tooltip_label.place(
        x=event.x_root - root.winfo_rootx() + 15,
        y=event.y_root - root.winfo_rooty() + 15
    )


def move_tooltip(event):

    widget = event.widget

    if hasattr(widget, "tooltip_label"):

        widget.tooltip_label.place(
            x=event.x_root - root.winfo_rootx() + 15,
            y=event.y_root - root.winfo_rooty() + 15
        )


def hide_tooltip(event):

    widget = event.widget

    if hasattr(widget, "tooltip_label"):
        widget.tooltip_label.destroy()

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
root.configure(bg=BG)

main_frame = tk.Frame(
    root,
    bg=BG
)

hotkey_frame = tk.Frame(
    root,
    bg=BG
)

social_frame = tk.Frame(
    root,
    bg=BG
)
donate_frame = tk.Frame(
    root,
    bg=BG
)
social_frame.place(x=800, y=10)

root.title("'INVASIO' - OCR Tool by Flex Air")
root.geometry("1000x600")

title_label = tk.Label(
    main_frame,
    text="INVASIO OCR TOOL",
    font=("Segoe UI", 26, "bold"),
    bg=BG,
    fg=TEXT
)

title_label.pack(pady=(10, 0))

subtitle_label = tk.Label(
    main_frame,
    text="Fast OCR for Mobile Screens by IK of Flex Air",
    font=("Segoe UI", 10),
    bg=BG,
    fg="#aaaaaa"
)

subtitle_label.pack(pady=(0, 15))

btc_icon = tk.PhotoImage(file="icons/btc_icon.png")
# noinspection SpellCheckingInspection
eth_icon = tk.PhotoImage(file="icons/etherium_icon.png")
bnb_icon = tk.PhotoImage(file="icons/bnb_icon.png")
sol_icon = tk.PhotoImage(file="icons/solana_icon.png")
ton_icon = tk.PhotoImage(file="icons/ton_icon.png")
tron_icon = tk.PhotoImage(file="icons/tron_icon.png")

# noinspection SpellCheckingInspection
DONATE_DATA = [
    ("BTC", btc_icon, "bc1qnjv8d2ecf3uwwugdf3jlxyc020e2ztc8s0zghv"),
    ("ETH (any token)", eth_icon, "0x108e08febfbe3e47a9c15e484fd6587f4a0c6279"),
    ("BNB (any token)", bnb_icon, "0x108e08febfbe3e47a9c15e484fd6587f4a0c6279"),
    ("SOL (any token)", sol_icon, "GEgnqADD4WJTDz1syRMyaK9qjn2jhhEknhreoZwWXT9T"),
    ("TON (any token)", ton_icon, "UQBZb8OHkXr08m1CWM_eGX40TMbeIUAVEWQeMLKl8RWZ2462"),
    ("TRX (any token)", tron_icon, "TJxdGZTtp9MeXF2EijYAR4BK5wNH99kJgW"),
]

copy_icon = tk.PhotoImage(file="icons/Copy_icon.png")

telegram_icon = tk.PhotoImage(
    file=os.path.join("icons", "telegram_icon.png")
)
youtube_icon = tk.PhotoImage(
    file=os.path.join("icons", "YT_icon.png")
)

# =========================
# GUI WINDOW CONFIG
# =========================
status_label = tk.Label(
    main_frame,
    text="Ready",
    font=("Arial", 30),
    bg=BG,
    fg=ACCENT
)
status_label.pack(pady=10)

btn_condition = tk.Button(
    main_frame,
    text="Добавить условие/Add Condition",
    width=35,
    font=("Arial", 18),
    command=gui_add_condition,
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_condition.pack(pady=5)

btn_option = tk.Button(
    main_frame,
    text="Добавить вариант/Add option",
    width=35,
    font=("Arial", 18),
    command=gui_add_option,
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_option.pack(pady=5)

btn_finish = tk.Button(
    main_frame,
    text="Собрать результат/Final Result",
    width=35,
    font=("Arial", 18),
    command=gui_finish,
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_finish.pack(pady=5)

btn_clear = tk.Button(
    main_frame,
    text="Очистить все/Clear Selection",
    width=35,
    font=("Arial", 18),
    command=clear_all,
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_clear.pack(pady=5)

preview_label = tk.Label(
    main_frame,
    text="Предпросмотр",
    font=("Arial", 15),
    bg=BG,
    fg=TEXT
)
preview_label.pack(pady=(15,5))

current_screen = "main"

def show_donate():
    global current_screen
    current_screen = "donate"

    main_frame.pack_forget()
    hotkey_frame.pack_forget()
    build_donate_screen()

    donate_frame.pack(fill="both", expand=True)

btn_donate = tk.Button(
    main_frame,
    text="Donate",
    font=("Arial", 15),
    command=show_donate,
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_donate.place(x=110, y=10)

# =========================
# SOCIALS
# =========================
socials_row = tk.Frame(
    social_frame,
    bg=BG
)
socials_row.pack(anchor="w", pady=2)

btn_telegram=tk.Button(
    socials_row,
    image=telegram_icon,
    command=lambda: open_link(TELEGRAM_URL),
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_telegram.pack(side="left")

btn_copy_tg = tk.Button(
    socials_row,
    image=copy_icon,
    command=lambda: copy_link(TELEGRAM_URL),
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_copy_tg.pack(side="left", padx=5)

btn_youtube = tk.Button(
    socials_row,
    image=youtube_icon,
    command=lambda: open_link(YOUTUBE_URL),
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_youtube.pack(side="left", padx=(20, 0))

btn_copy_yt = tk.Button(
    socials_row,
    image=copy_icon,
    command=lambda: copy_link(YOUTUBE_URL),
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
btn_copy_yt.pack(side="left", padx=5)

btn_telegram.image = telegram_icon
btn_youtube.image = youtube_icon
btn_copy_tg.image = copy_icon
btn_copy_yt.image = copy_icon

# =========================
# HOTKEYS
# =========================
hotkeys = {
    "condition": "F1",
    "option": "F2",
    "finish": "F3",
    "clear": "F4"
}
SETTINGS_FILE = "settings.json"

def save_settings():
    data = {
        "hotkeys": hotkeys
    }
    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

def load_settings():
    global hotkeys

    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)
            if "hotkeys" in data:
                hotkeys.update(data["hotkeys"])

    except (FileNotFoundError, json.JSONDecodeError):
        save_settings()

load_settings()

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
    frame = tk.Frame(
        hotkey_frame,
        cursor="hand2",
        bg=CARD,
        relief="flat",
        borderwidth=0
    )
    frame.pack(pady=5)

    tk.Label(
        frame,
        text=label,
        width=20,
        anchor="w",
        bg=CARD,
        fg=TEXT,
        activebackground=BTN_HOVER,
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        cursor="hand2"
    ).pack(side="left")

    key_label = tk.Label(
        frame,
        text=hotkeys[action],
        width=25,
        bg=CARD,
        fg=TEXT,
        activebackground=BTN_HOVER,
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        cursor="hand2"
    )
    key_label.pack(side="left")

    def start_rebind():
        begin_hotkey_capture(action, key_label)

    tk.Button(
        frame,
        text="Change",
        command=start_rebind,
        bg=BTN,
        fg=TEXT,
        activebackground=BTN_HOVER,
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        cursor="hand2"
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
            label_widget.config(text=hotkeys[action])
            waiting_hotkey_action = None
            return

        hotkeys[action] = new_key
        save_settings()
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
frame = tk.Frame(main_frame, bg=CARD)
frame.pack(fill="both", expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(frame, bg=BTN, troughcolor=BG)

preview_text = tk.Text(
    frame,
    font=("Consolas", 11),
    bg="#252526",
    fg="#d4d4d4",
    insertbackground="white",
    relief="flat",
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
    tk.Label(
        hotkey_frame,
        text="Hotkey Settings",
        font=("Segoe UI", 20, "bold"),
        bg=BG,
        fg=TEXT
    ).pack(pady=10)

    create_hotkey_row("Condition", "condition")
    create_hotkey_row("Option", "option")
    create_hotkey_row("Finish", "finish")
    create_hotkey_row("Clear", "clear")

    tk.Button(
        hotkey_frame,
        text="Назад/Back",
        command=show_main,
        font=("Arial", 15),
        bg=BTN,
        fg=TEXT,
        activebackground=BTN_HOVER,
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        cursor="hand2"
    ).pack(pady=20)

def show_main():
    global current_screen
    current_screen = "main"
    donate_frame.pack_forget()
    hotkey_frame.pack_forget()
    main_frame.pack(fill="both", expand=True)

def show_hotkeys():
    global current_screen
    current_screen = "hotkeys"
    main_frame.pack_forget()
    build_hotkey_screen()
    hotkey_frame.pack(fill="both", expand=True)

def on_esc(event):
    if current_screen != "main":
        show_main()
    if waiting_hotkey_action is not None:
        return

# =========================
# DONATE SCREEN
# =========================
def build_donate_screen():
    for w in donate_frame.winfo_children():
        w.destroy()

    tk.Label(
        donate_frame,
        text="Донаты/Donations",
        font = ("Segoe UI", 26, "bold"),
        bg = BG,
        fg = TEXT
    ).pack(pady=10)

    for name, icon, address in DONATE_DATA:
        row = tk.Frame(
            donate_frame,
            cursor="hand2",
            bg=CARD,
            borderwidth=0
        )
        row.pack(anchor="center", pady=5)

        icon_label = tk.Label(
            row,
            image=icon,
            fg=TEXT,
            cursor="hand2",
            bg=CARD,
            borderwidth=0
        )
        icon_label.pack(side="left", padx=5)

        addr_label = tk.Label(
            row,
            text=address,
            fg=TEXT,
            cursor="hand2",
            font=("Consolas", 11),
            bg=BTN_HOVER,
            activebackground=BTN_HOVER,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0
        )
        addr_label.pack(side="left", padx=5)

        addr_label.bind(
            "<Enter>",
            lambda e: show_tooltip(
                e,
                "Copy to clipboard"
            )
        )

        addr_label.bind(
            "<Leave>",
            hide_tooltip
        )

        addr_label.bind(
            "<Motion>",
            move_tooltip
        )

        addr_label.bind(
            "<Button-1>",
            lambda e,
                   addr=address,
                   w=addr_label:
            copy_address(addr, w)
        )

    tk.Button(
        donate_frame,
        text="Назад/Back",
        command=show_main,
        font=("Arial", 15),
        bg=BTN,
        fg=TEXT,
        activebackground=BTN_HOVER,
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        cursor="hand2"
    ).pack(pady=20)

hotkey_btn = tk.Button(
    main_frame,
    text="Hotkeys",
    command=show_hotkeys,
    font = ("Arial", 15),
    bg=BTN,
    fg=TEXT,
    activebackground=BTN_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)
hotkey_btn.place(x=10, y=10)

root.bind("<Escape>", on_esc)
root.bind("<Key>", key_handler)
root.focus_set()
main_frame.pack(fill="both", expand=True)

root.mainloop()