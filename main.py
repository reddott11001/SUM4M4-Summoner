import os
import re
import sys
import threading
import time
import webbrowser
import random

import customtkinter as ctk
import pyautogui
from PIL import Image, ImageTk

# Persistent Counter Logic
SAVE_FILE = os.path.join(os.getenv("APPDATA", ""), "neon_url_opener_count.txt")
if not os.path.exists(SAVE_FILE) and not os.getenv("APPDATA"):
    SAVE_FILE = "neon_url_opener_count.txt"


def load_count():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                return int(f.read().strip())
    except:
        pass
    return 0


def save_count(n):
    try:
        with open(SAVE_FILE, "w") as f:
            f.write(str(n))
    except:
        pass


def format_count(n):
    if n >= 1000000:
        return f"{n / 1000000:.1f}M".replace(".0M", "M")
    elif n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def parse_amount(val):
    val = val.strip().lower()
    if not val:
        return 1
    try:
        if val.endswith("k"):
            return int(float(val[:-1]) * 1000)
        elif val.endswith("m"):
            return int(float(val[:-1]) * 1000000)
        return int(val)
    except ValueError:
        return 1


def parse_single_time(val):
    val = val.strip().lower()
    if not val:
        return 2.0
    try:
        if val.endswith("m"):
            return float(val[:-1]) * 60.0
        elif val.endswith("s"):
            return float(val[:-1])
        return float(val)
    except ValueError:
        return 2.0


def parse_time(val):
    val = val.strip().lower()
    if not val:
        return ("fixed", 2.0)  # default 2 seconds if left blank
        
    match = re.match(r"^random\s*\(\s*([^\,]+)\s*,\s*([^\)]+)\s*\)$", val)
    if match:
        min_val = parse_single_time(match.group(1))
        max_val = parse_single_time(match.group(2))
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        return ("random", min_val, max_val)

    return ("fixed", parse_single_time(val))


# Reset counter to 0 on application startup
total_opened = 0
save_count(0)

is_processing = False
is_paused = False

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def open_url(event=None):
    global is_processing, total_opened, is_paused
    if is_processing:
        # If they click while processing, we stop it!
        is_processing = False
        is_paused = False
        open_btn.configure(text="STOPPING...", state="disabled")
        pause_btn.configure(state="disabled", text="PAUSE")

        # Reset the web count when stopped
        total_opened = 0
        save_count(total_opened)
        count_label.configure(text=f"Total URLs Opened: {format_count(total_opened)}")
        return

    url = url_entry.get().strip()
    amount_str = amount_entry.get().strip()
    amount = parse_amount(amount_str)

    timer_str = timer_entry.get().strip()
    delay_config = parse_time(timer_str)

    if url:
        # Check if URL starts with http:// or https://
        if not re.match(r"^https?://", url):
            url = "https://" + url

        is_processing = True
        is_paused = False
        open_btn.configure(text="STOP PROCESSING (Click to abort)")
        pause_btn.configure(state="normal", text="PAUSE")

        # Start a background thread so the GUI doesn't freeze
        threading.Thread(
            target=process_loop, args=(url, amount, delay_config), daemon=True
        ).start()


def toggle_pause():
    global is_paused, is_processing
    if not is_processing:
        return
    is_paused = not is_paused
    if is_paused:
        pause_btn.configure(text="RESUME", text_color="#00FF00", border_color="#00FF00")
        open_btn.configure(text="PAUSED (Click to stop)")
    else:
        pause_btn.configure(text="PAUSE", text_color=NEON_RED, border_color=NEON_RED)
        open_btn.configure(text="RESUMING...")


def process_loop(url, amount, delay_config):
    global total_opened, is_processing, is_paused

    for i in range(amount):
        while is_paused and is_processing:
            time.sleep(0.5)

        if not is_processing:  # User cancelled
            break

        # Open in default web browser. If amount > 1, we must let browser get focus for ctrl+w to work
        autoraise_val = True if amount > 1 else False
        webbrowser.open(url, new=2, autoraise=autoraise_val)

        # If opening multiple tabs, wait 'delay' seconds for page to load/stay open, then send 'ctrl+w'
        if amount > 1:
            if delay_config[0] == "random":
                delay = random.uniform(delay_config[1], delay_config[2])
            else:
                delay = delay_config[1]

            # We break the sleep into small chunks so we can interrupt it if user clicks STOP
            sleep_time = delay
            while sleep_time > 0 and is_processing:
                if is_paused:
                    time.sleep(0.5)
                    continue
                time.sleep(min(0.5, sleep_time))
                sleep_time -= 0.5

            if not is_processing:
                break

            pyautogui.hotkey("ctrl", "w")
            time.sleep(0.3)  # Small delay before next loop iteration

        # Update counter
        total_opened += 1
        save_count(total_opened)

        # Safely update the GUI from the background thread
        app.after(
            0,
            lambda current=i + 1: count_label.configure(
                text=f"Total URLs Opened: {format_count(total_opened)}"
            ),
        )

        if amount > 1:
            app.after(
                0,
                lambda current=i + 1: open_btn.configure(
                    text=f"PROCESSING... {current}/{amount}"
                ) if not is_paused else None,
            )

    # Cleanup when done
    is_processing = False
    is_paused = False
    app.after(0, lambda: open_btn.configure(state="normal", text="OPEN IN NEW TAB"))
    app.after(0, lambda: pause_btn.configure(state="disabled", text="PAUSE", text_color=NEON_RED, border_color=NEON_RED))

    # Bring app back to the front
    app.after(100, bring_to_front)
    app.after(500, bring_to_front)


def bring_to_front():
    # Force the window to the very top, grab focus, then release the topmost lock
    app.attributes("-topmost", True)
    app.focus_force()
    app.attributes("-topmost", False)


def get_resource_path(relative_path):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Create main window
app = ctk.CTk()
app.title("SUM4M4 Summoner")
app.resizable(False, False)  # Tidak bisa di-resize
app.configure(fg_color="#050505")  # Deep black background

# Background Image Logic
bg_path = get_resource_path("BACKGR.png")
if os.path.exists(bg_path):
    bg_img = Image.open(bg_path)
    # Mengecilkan background 2x lipat (Setengah dari ukuran asli)
    bg_w, bg_h = bg_img.size
    bg_w = bg_w // 2
    bg_h = bg_h // 2
    bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)

    app.geometry(f"{bg_w}x{bg_h}")

    bg_photo = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(bg_w, bg_h))
    bg_label = ctk.CTkLabel(app, image=bg_photo, text="")
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    parent_container = bg_label
else:
    app.geometry("300x450")  # Default size yang sudah dikecilkan
    parent_container = app


# Set app icon if available
icon_path = get_resource_path("icon.ico")
if not os.path.exists(icon_path):
    icon_path = get_resource_path("icon.png")

if os.path.exists(icon_path):
    try:
        if icon_path.endswith(".ico"):
            app.iconbitmap(icon_path)
        else:
            app.iconphoto(False, ImageTk.PhotoImage(Image.open(icon_path)))
    except Exception as e:
        pass

# Neon color palette
NEON_RED = "#FF073A"
TEXT_COLOR = "#FFFFFF"
BG_COLOR = "#0A0A0A"
FRAME_BG = "#121212"

# Container frame for styling
frame = ctk.CTkFrame(
    parent_container,
    fg_color=FRAME_BG,
    bg_color="transparent",
    border_color=NEON_RED,
    border_width=2,
    corner_radius=15,
)
frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

# Title Label
title_label = ctk.CTkLabel(
    frame,
    text="SUM4M4 SUMMONER",
    font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
    text_color=NEON_RED,
)
title_label.pack(pady=(20, 15), padx=30)

# URL Input Entry
url_entry = ctk.CTkEntry(
    frame,
    placeholder_text="Enter your link here...",
    width=250,
    height=35,
    font=ctk.CTkFont(family="Consolas", size=13),
    text_color=TEXT_COLOR,
    fg_color=BG_COLOR,
    border_color=NEON_RED,
    border_width=2,
    corner_radius=8,
    placeholder_text_color="#555555",
)
url_entry.pack(pady=(0, 10), padx=30)

# Amount Input Entry
amount_entry = ctk.CTkEntry(
    frame,
    placeholder_text="Amount (e.g. 1, 10, 1k)...",
    width=250,
    height=35,
    font=ctk.CTkFont(family="Consolas", size=13),
    text_color=TEXT_COLOR,
    fg_color=BG_COLOR,
    border_color=NEON_RED,
    border_width=2,
    corner_radius=8,
    placeholder_text_color="#555555",
)
amount_entry.pack(pady=(0, 10), padx=30)

# Timer Input Entry
timer_entry = ctk.CTkEntry(
    frame,
    placeholder_text="Time (e.g. 60s, random(1,5))...",
    width=250,
    height=35,
    font=ctk.CTkFont(family="Consolas", size=13),
    text_color=TEXT_COLOR,
    fg_color=BG_COLOR,
    border_color=NEON_RED,
    border_width=2,
    corner_radius=8,
    placeholder_text_color="#555555",
)
timer_entry.pack(pady=(0, 15), padx=30)
timer_entry.bind("<Return>", open_url)

# Button Frame
btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
btn_frame.pack(pady=(0, 15), padx=30)

# Open Button
open_btn = ctk.CTkButton(
    btn_frame,
    text="OPEN IN NEW TAB",
    width=140,
    height=35,
    font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
    fg_color=BG_COLOR,
    text_color=NEON_RED,
    hover_color=NEON_RED,
    border_color=NEON_RED,
    border_width=2,
    corner_radius=8,
    command=open_url,
)
open_btn.pack(side="left", padx=(0, 5))

# Pause Button
pause_btn = ctk.CTkButton(
    btn_frame,
    text="PAUSE",
    width=60,
    height=35,
    font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
    fg_color=BG_COLOR,
    text_color=NEON_RED,
    hover_color=NEON_RED,
    border_color=NEON_RED,
    border_width=2,
    corner_radius=8,
    command=toggle_pause,
    state="disabled"
)
pause_btn.pack(side="left", padx=(5, 0))

# Count Label
count_label = ctk.CTkLabel(
    frame,
    text=f"Total URLs Opened: {format_count(total_opened)}",
    font=ctk.CTkFont(family="Consolas", size=11),
    text_color="#888888",  # Grey color for subtitle aesthetic
)
count_label.pack(pady=(0, 15))


# Add hover effect for neon glow inversion
def on_enter_open(e):
    if not is_processing:
        open_btn.configure(text_color="#000000")

def on_leave_open(e):
    open_btn.configure(text_color=NEON_RED)

def on_enter_pause(e):
    if pause_btn._state != "disabled":
        pause_btn.configure(text_color="#000000")

def on_leave_pause(e):
    if is_paused:
        pause_btn.configure(text_color="#00FF00")
    else:
        pause_btn.configure(text_color=NEON_RED)

open_btn.bind("<Enter>", on_enter_open)
open_btn.bind("<Leave>", on_leave_open)
pause_btn.bind("<Enter>", on_enter_pause)
pause_btn.bind("<Leave>", on_leave_pause)

# Copyright Label
copyright_label = ctk.CTkLabel(
    parent_container,
    text="© Reddott11001",
    font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
    text_color="#666666",
    fg_color="transparent",
    bg_color="transparent"
)
copyright_label.place(relx=0.96, rely=0.98, anchor="se")

# Run the app
app.mainloop()
