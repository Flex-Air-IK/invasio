import subprocess
import json
import os
import webbrowser

import cv2
import pytesseract
import pyperclip
import tkinter as tk
from tkinter import messagebox
from PIL import Image


# ===========================================================================
# CONFIGURATION
# ===========================================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SETTINGS_FILE = "settings.json"

TELEGRAM_URL = "https://t.me/IK_Flex_Air"
YOUTUBE_URL  = "https://www.youtube.com/@FlexAir-pwn"

# Color theme
BG           = "#1e1e1e"   # window background
CARD         = "#2d2d2d"   # cards / panels
BTN          = "#3a3a3a"   # buttons
BTN_HOVER    = "#505050"   # buttons on hover
TEXT         = "#ffffff"   # white text
ACCENT       = "#4CAF50"   # green accent
PREVIEW_BG   = "#252526"   # preview background
PREVIEW_TEXT = "#d4d4d4"   # preview text


# ===========================================================================
# APPLICATION STATE
# ===========================================================================

condition_texts:    list[str] = []
options:            list[str] = []
option_index:       int       = 0
mode:               str       = "condition"
last_text:          str       = ""
waiting_hotkey_action         = None   # (action, label_widget) | None
current_screen:     str       = "main"

hotkeys: dict[str, str] = {
    "condition": "F1",
    "option":    "F2",
    "finish":    "F3",
    "clear":     "F4",
}


# ===========================================================================
# SETTINGS  (load / save)
# ===========================================================================

def save_settings() -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"hotkeys": hotkeys}, f, ensure_ascii=False, indent=4)


def load_settings() -> None:
    global hotkeys
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "hotkeys" in data:
                hotkeys.update(data["hotkeys"])
    except (FileNotFoundError, json.JSONDecodeError):
        save_settings()


# ===========================================================================
# OCR PIPELINE
# ===========================================================================

def make_screenshot() -> None:
    """Capture a screenshot from the connected Android device via ADB."""
    with open("screen.png", "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f)


def select_roi_scaled(image_path: str, scale: float = 0.5) -> str:
    """
    Show a scaled-down preview so the user can draw an ROI,
    then crop the original-resolution image to that region.
    Returns the path to the saved crop ("cropped.png").
    """
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    preview = cv2.resize(img, (int(w * scale), int(h * scale)))
    r = cv2.selectROI("Select area (ENTER to confirm)", preview, False, False)
    cv2.destroyAllWindows()

    x, y, w_roi, h_roi = r
    # Scale coordinates back to the original resolution
    x,     y     = int(x     / scale), int(y     / scale)
    w_roi, h_roi = int(w_roi / scale), int(h_roi / scale)

    cropped = img[y : y + h_roi, x : x + w_roi]
    cv2.imwrite("cropped.png", cropped)
    return "cropped.png"


def ocr(image_path: str) -> str:
    """Run Tesseract OCR (English + Russian) on the given image."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="eng+rus")


def clean_text(text: str) -> str:
    """Strip whitespace and remove blank lines."""
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def remove_overlap(new_text: str, prev_text: str) -> str:
    """
    Remove lines at the start of *new_text* that are already present
    at the end of *prev_text* (handles scroll overlap).
    """
    if not prev_text:
        return new_text

    new_lines  = new_text.split("\n")
    last_lines = prev_text.split("\n")

    overlap = 0
    for i in range(1, min(len(new_lines), len(last_lines)) + 1):
        if new_lines[:i] == last_lines[-i:]:
            overlap = i

    return "\n".join(new_lines[overlap:])


def handle_option(text: str) -> None:
    """Append a numbered option to the options list."""
    global option_index

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return

    option_index += 1
    options.append(f"{option_index}) {' '.join(lines)}")
    print(f"OPTION {option_index} ADDED")


def pipeline() -> None:
    """
    Full OCR pipeline:
      screenshot → ROI selection → OCR → clean → de-duplicate → store.
    """
    global last_text

    print(f"Screenshot in mode: {mode}")

    make_screenshot()
    cropped_path = select_roi_scaled("screen.png")
    raw_text     = ocr(cropped_path)
    cleaned      = clean_text(raw_text)
    processed    = remove_overlap(cleaned, last_text)
    last_text    = cleaned

    if mode == "condition":
        condition_texts.append(processed)
        print("CONDITION ADDED")
    elif mode == "options":
        handle_option(processed)


# ===========================================================================
# MODE
# ===========================================================================

def switch_mode(new_mode: str) -> None:
    global mode
    mode = new_mode
    print(f"\n MODE: {mode}\n")


# ===========================================================================
# RESULT  (assemble & copy)
# ===========================================================================

def finish() -> None:
    """Combine conditions + options, copy to clipboard, then reset state."""
    global option_index, last_text

    condition_block = "\n".join(condition_texts)
    options_block   = "\n".join(options)
    result          = f"{condition_block}\n\n{options_block}"

    pyperclip.copy(result)
    print("\nFINAL RESULT:\n", result, "\nCopied to clipboard!\n")

    condition_texts.clear()
    options.clear()
    option_index = 0
    last_text    = ""


# ===========================================================================
# GUI — BUTTON ACTIONS
# ===========================================================================

def gui_add_condition() -> None:
    switch_mode("condition")
    pipeline()
    refresh_ui()


def gui_add_option() -> None:
    switch_mode("options")
    pipeline()
    refresh_ui()


def gui_finish() -> None:
    finish()
    refresh_ui()
    status_label.config(text="✓ Result copied to clipboard!", fg=ACCENT)


def clear_all() -> None:
    global option_index, last_text

    condition_texts.clear()
    options.clear()
    option_index = 0
    last_text    = ""

    preview_text.delete("1.0", tk.END)
    refresh_ui()


# ===========================================================================
# GUI — REFRESH HELPERS
# ===========================================================================

def update_preview() -> None:
    preview = "\n".join(condition_texts)
    if options:
        preview += "\n\n" + "\n".join(options)

    preview_text.delete("1.0", tk.END)
    preview_text.insert(tk.END, preview)


def refresh_ui() -> None:
    update_preview()
    status_label.config(
        text=f"Condition fragments: {len(condition_texts)} | Options: {len(options)}",
        fg=ACCENT,
    )


def refresh_hotkey_labels() -> None:
    btn_condition.config(text=f"[{hotkeys['condition']}] Добавить условие/Add Condition")
    btn_option.config(   text=f"[{hotkeys['option']}]    Добавить вариант/Add Option")
    btn_finish.config(   text=f"[{hotkeys['finish']}]    Собрать результат/Final Result")
    btn_clear.config(    text=f"[{hotkeys['clear']}]     Очистить все/Clear Selection")


# ===========================================================================
# GUI — LINKS & CLIPBOARD UTILITIES
# ===========================================================================

def open_link(url: str) -> None:
    webbrowser.open(url)


def copy_link(url: str) -> None:
    pyperclip.copy(url)
    messagebox.showinfo("Copied", "Link copied to clipboard")


def copy_address(address: str, widget: tk.Widget) -> None:
    pyperclip.copy(address)
    widget.tooltip_label.config(text="Copied!")
    widget.after(1500, lambda: widget.tooltip_label.config(text="Copy to clipboard"))


# ===========================================================================
# GUI — TOOLTIP
# ===========================================================================

def show_tooltip(event: tk.Event, text: str) -> None:
    widget = event.widget
    widget.tooltip_label = tk.Label(
        root, text=text,
        bg="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9),
    )
    widget.tooltip_label.place(
        x=event.x_root - root.winfo_rootx() + 15,
        y=event.y_root - root.winfo_rooty() + 15,
    )


def move_tooltip(event: tk.Event) -> None:
    widget = event.widget
    if hasattr(widget, "tooltip_label"):
        widget.tooltip_label.place(
            x=event.x_root - root.winfo_rootx() + 15,
            y=event.y_root - root.winfo_rooty() + 15,
        )


def hide_tooltip(event: tk.Event) -> None:
    widget = event.widget
    if hasattr(widget, "tooltip_label"):
        widget.tooltip_label.destroy()


# ===========================================================================
# GUI — HOTKEY MANAGEMENT
# ===========================================================================

def is_key_taken(key: str, ignore_action: str | None = None) -> bool:
    return any(k == key for action, k in hotkeys.items() if action != ignore_action)


def set_hotkey(action: str, key: str) -> None:
    key = key.strip().upper()
    if not key:
        return
    if is_key_taken(key, ignore_action=action):
        messagebox.showwarning(
            "Кнопка уже назначена/Hotkey already used",
            f"{key} уже назначена!/{key} already assigned!",
        )
        return
    hotkeys[action] = key
    refresh_hotkey_labels()
    refresh_ui()


def begin_hotkey_capture(action: str, label_widget: tk.Label) -> None:
    global waiting_hotkey_action
    waiting_hotkey_action = (action, label_widget)
    label_widget.config(text="Нажми клавишу/Press a key...")


def key_handler(event: tk.Event) -> None:
    global waiting_hotkey_action

    # ── Hotkey rebind mode ──────────────────────────────────────────────────
    if waiting_hotkey_action is not None:
        action, label_widget = waiting_hotkey_action
        new_key = event.keysym

        if new_key == "Escape":
            return

        if is_key_taken(new_key, ignore_action=action):
            messagebox.showwarning(
                "Кнопка уже назначена/Button is already in use",
                f"{new_key} уже используется!/{new_key} already in use!",
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

    # ── Normal hotkey dispatch (main screen only) ───────────────────────────
    if current_screen != "main":
        return

    key = event.keysym
    if   key == hotkeys["condition"]: gui_add_condition()
    elif key == hotkeys["option"]:    gui_add_option()
    elif key == hotkeys["finish"]:    gui_finish()
    elif key == hotkeys["clear"]:     clear_all()


# ===========================================================================
# GUI — SCREEN NAVIGATION
# ===========================================================================

def show_main() -> None:
    global current_screen
    current_screen = "main"
    donate_frame.pack_forget()
    hotkey_frame.pack_forget()
    main_frame.pack(fill="both", expand=True)


def show_hotkeys() -> None:
    global current_screen
    current_screen = "hotkeys"
    main_frame.pack_forget()
    build_hotkey_screen()
    hotkey_frame.pack(fill="both", expand=True)


def show_donate() -> None:
    global current_screen
    current_screen = "donate"
    main_frame.pack_forget()
    hotkey_frame.pack_forget()
    build_donate_screen()
    donate_frame.pack(fill="both", expand=True)


def on_esc(event: tk.Event) -> None:
    if current_screen != "main":
        show_main()
    # If waiting for a hotkey capture, Escape is handled inside key_handler


# ===========================================================================
# GUI — HOTKEY SETTINGS SCREEN
# ===========================================================================

def create_hotkey_row(label: str, action: str) -> None:
    frame = tk.Frame(hotkey_frame, cursor="hand2", bg=CARD, relief="flat", borderwidth=0)
    frame.pack(pady=5)

    tk.Label(
        frame, text=label, width=20, anchor="w",
        bg=CARD, fg=TEXT, relief="flat", borderwidth=0, cursor="hand2",
    ).pack(side="left")

    key_label = tk.Label(
        frame, text=hotkeys[action], width=25,
        bg=CARD, fg=TEXT, relief="flat", borderwidth=0, cursor="hand2",
    )
    key_label.pack(side="left")

    tk.Button(
        frame, text="Change",
        command=lambda: begin_hotkey_capture(action, key_label),
        bg=BTN, fg=TEXT, activebackground=BTN_HOVER, activeforeground=TEXT,
        relief="flat", borderwidth=0, cursor="hand2",
    ).pack(side="left")


def build_hotkey_screen() -> None:
    for widget in hotkey_frame.winfo_children():
        widget.destroy()

    tk.Label(
        hotkey_frame, text="Hotkey Settings",
        font=("Segoe UI", 20, "bold"), bg=BG, fg=TEXT,
    ).pack(pady=10)

    create_hotkey_row("Condition", "condition")
    create_hotkey_row("Option",    "option")
    create_hotkey_row("Finish",    "finish")
    create_hotkey_row("Clear",     "clear")

    tk.Button(
        hotkey_frame, text="Назад/Back", command=show_main,
        font=("Arial", 15), bg=BTN, fg=TEXT,
        activebackground=BTN_HOVER, activeforeground=TEXT,
        relief="flat", borderwidth=0, cursor="hand2",
    ).pack(pady=20)


# ===========================================================================
# GUI — DONATE SCREEN
# ===========================================================================

def build_donate_screen() -> None:
    for widget in donate_frame.winfo_children():
        widget.destroy()

    tk.Label(
        donate_frame, text="Донаты/Donations",
        font=("Segoe UI", 26, "bold"), bg=BG, fg=TEXT,
    ).pack(pady=10)

    for name, icon, address in DONATE_DATA:
        row = tk.Frame(donate_frame, cursor="hand2", bg=CARD, borderwidth=0)
        row.pack(anchor="center", pady=5)

        tk.Label(row, image=icon, fg=TEXT, cursor="hand2", bg=CARD, borderwidth=0).pack(
            side="left", padx=5
        )
        if name != "BTC":
            tk.Label(row, text="(Chain address - send any token)", fg=TEXT, cursor="hand2", bg=CARD, borderwidth=0).pack(
                side="left", padx=5
            )

        addr_label = tk.Label(
            row, text=address, fg=TEXT, cursor="hand2",
            font=("Consolas", 11), bg=BTN_HOVER,
            activebackground=BTN_HOVER, activeforeground=TEXT,
            relief="flat", borderwidth=0,
        )
        addr_label.pack(side="left", padx=5)

        addr_label.bind("<Enter>",   lambda e: show_tooltip(e, "Copy to clipboard"))
        addr_label.bind("<Leave>",   hide_tooltip)
        addr_label.bind("<Motion>",  move_tooltip)
        addr_label.bind(
            "<Button-1>",
            lambda e, addr=address, w=addr_label: copy_address(addr, w),
        )

    tk.Button(
        donate_frame, text="Назад/Back", command=show_main,
        font=("Arial", 15), bg=BTN, fg=TEXT,
        activebackground=BTN_HOVER, activeforeground=TEXT,
        relief="flat", borderwidth=0, cursor="hand2",
    ).pack(pady=20)


# ===========================================================================
# GUI — WINDOW CONSTRUCTION
# ===========================================================================

# ── Root window ─────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("'INVASIO' - OCR Tool by Flex Air")
root.geometry("1000x600")
root.configure(bg=BG)

# ── Top-level frames ─────────────────────────────────────────────────────────
main_frame   = tk.Frame(root, bg=BG)
hotkey_frame = tk.Frame(root, bg=BG)
donate_frame = tk.Frame(root, bg=BG)
social_frame = tk.Frame(root, bg=BG)
social_frame.place(x=800, y=10)

# ── Icons ────────────────────────────────────────────────────────────────────
btc_icon      = tk.PhotoImage(file="icons/btc_icon.png")
eth_icon      = tk.PhotoImage(file="icons/etherium_icon.png")
bnb_icon      = tk.PhotoImage(file="icons/bnb_icon.png")
sol_icon      = tk.PhotoImage(file="icons/solana_icon.png")
ton_icon      = tk.PhotoImage(file="icons/ton_icon.png")
tron_icon     = tk.PhotoImage(file="icons/tron_icon.png")
copy_icon     = tk.PhotoImage(file="icons/Copy_icon.png")
telegram_icon = tk.PhotoImage(file=os.path.join("icons", "telegram_icon.png"))
youtube_icon  = tk.PhotoImage(file=os.path.join("icons", "YT_icon.png"))

# ── Donate data (must come after icons are loaded) ───────────────────────────
DONATE_DATA = [
    ("BTC",            btc_icon,  "bc1qnjv8d2ecf3uwwugdf3jlxyc020e2ztc8s0zghv"),
    ("ETH", eth_icon, "0x108e08febfbe3e47a9c15e484fd6587f4a0c6279"),
    ("BNB", bnb_icon, "0x108e08febfbe3e47a9c15e484fd6587f4a0c6279"),
    ("SOL", sol_icon, "GEgnqADD4WJTDz1syRMyaK9qjn2jhhEknhreoZwWXT9T"),
    ("TON", ton_icon, "UQBZb8OHkXr08m1CWM_eGX40TMbeIUAVEWQeMLKl8RWZ2462"),
    ("TRX", tron_icon,"TJxdGZTtp9MeXF2EijYAR4BK5wNH99kJgW"),
]

# ── Main frame: header ────────────────────────────────────────────────────────
tk.Label(
    main_frame, text="INVASIO OCR TOOL",
    font=("Segoe UI", 26, "bold"), bg=BG, fg=TEXT,
).pack(pady=(10, 0))

tk.Label(
    main_frame, text="Fast OCR for Mobile Screens by IK of Flex Air",
    font=("Segoe UI", 10), bg=BG, fg="#aaaaaa",
).pack(pady=(0, 15))

# ── Main frame: status label ──────────────────────────────────────────────────
status_label = tk.Label(
    main_frame, text="Ready",
    font=("Arial", 30), bg=BG, fg=ACCENT,
)
status_label.pack(pady=10)

# ── Main frame: action buttons ────────────────────────────────────────────────
_btn_cfg = dict(
    width=35, font=("Arial", 18),
    bg=BTN, fg=TEXT,
    activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)

btn_condition = tk.Button(
    main_frame, text="Добавить условие/Add Condition",
    command=gui_add_condition, **_btn_cfg,
)
btn_condition.pack(pady=5)

btn_option = tk.Button(
    main_frame, text="Добавить вариант/Add option",
    command=gui_add_option, **_btn_cfg,
)
btn_option.pack(pady=5)

btn_finish = tk.Button(
    main_frame, text="Собрать результат/Final Result",
    command=gui_finish, **_btn_cfg,
)
btn_finish.pack(pady=5)

btn_clear = tk.Button(
    main_frame, text="Очистить все/Clear Selection",
    command=clear_all, **_btn_cfg,
)
btn_clear.pack(pady=5)

# ── Main frame: preview area ──────────────────────────────────────────────────
tk.Label(
    main_frame, text="Предпросмотр",
    font=("Arial", 15), bg=BG, fg=TEXT,
).pack(pady=(15, 5))

preview_frame = tk.Frame(main_frame, bg=CARD)
preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(preview_frame, bg=BTN, troughcolor=BG)
preview_text = tk.Text(
    preview_frame,
    font=("Consolas", 11), bg=PREVIEW_BG, fg=PREVIEW_TEXT,
    insertbackground="white", relief="flat",
    yscrollcommand=scrollbar.set,
)
scrollbar.config(command=preview_text.yview)
scrollbar.pack(side="right", fill="y")
preview_text.pack(side="left", fill="both", expand=True)

# ── Main frame: overlay buttons (Hotkeys / Donate) ───────────────────────────
hotkey_btn = tk.Button(
    main_frame, text="Hotkeys", command=show_hotkeys,
    font=("Arial", 15), bg=BTN, fg=TEXT,
    activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
hotkey_btn.place(x=10, y=10)

btn_donate = tk.Button(
    main_frame, text="Donate", command=show_donate,
    font=("Arial", 15), bg=BTN, fg=TEXT,
    activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
btn_donate.place(x=110, y=10)

# ── Social bar (top-right) ────────────────────────────────────────────────────
socials_row = tk.Frame(social_frame, bg=BG)
socials_row.pack(anchor="w", pady=2)

btn_telegram = tk.Button(
    socials_row, image=telegram_icon, command=lambda: open_link(TELEGRAM_URL),
    bg=BTN, fg=TEXT, activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
btn_telegram.pack(side="left")

btn_copy_tg = tk.Button(
    socials_row, image=copy_icon, command=lambda: copy_link(TELEGRAM_URL),
    bg=BTN, fg=TEXT, activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
btn_copy_tg.pack(side="left", padx=5)

btn_youtube = tk.Button(
    socials_row, image=youtube_icon, command=lambda: open_link(YOUTUBE_URL),
    bg=BTN, fg=TEXT, activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
btn_youtube.pack(side="left", padx=(20, 0))

btn_copy_yt = tk.Button(
    socials_row, image=copy_icon, command=lambda: copy_link(YOUTUBE_URL),
    bg=BTN, fg=TEXT, activebackground=BTN_HOVER, activeforeground=TEXT,
    relief="flat", borderwidth=0, cursor="hand2",
)
btn_copy_yt.pack(side="left", padx=5)

# Keep references so Tk doesn't garbage-collect the images
for btn, img in [
    (btn_telegram, telegram_icon),
    (btn_youtube,  youtube_icon),
    (btn_copy_tg,  copy_icon),
    (btn_copy_yt,  copy_icon),
]:
    btn.image = img


# ===========================================================================
# STARTUP
# ===========================================================================

load_settings()
refresh_hotkey_labels()

root.bind("<Escape>", on_esc)
root.bind("<Key>",    key_handler)
root.focus_set()

main_frame.pack(fill="both", expand=True)
root.mainloop()