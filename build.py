import os

import customtkinter
import PyInstaller.__main__

customtkinter_path = os.path.dirname(customtkinter.__file__)

print(f"CustomTkinter path: {customtkinter_path}")

# Default PyInstaller arguments
pyinstaller_args = [
    "main.py",
    "--name=SUM4M4_Summoner",
    "--noconfirm",
    "--windowed",
    "--onefile",
    f"--add-data={customtkinter_path};customtkinter/",
]

# Add icon if it exists
if os.path.exists("icon.ico"):
    print("Found icon.ico! Adding it to the executable...")
    pyinstaller_args.append("--icon=icon.ico")
    pyinstaller_args.append("--add-data=icon.ico;.")
elif os.path.exists("icon.png"):
    print("Found icon.png! Adding it to the executable...")
    pyinstaller_args.append("--icon=icon.png")
    pyinstaller_args.append("--add-data=icon.png;.")
else:
    print("icon not found! Building without custom icon.")

# Add background image if it exists
if os.path.exists("BACKGR.png"):
    print("Found BACKGR.png! Adding it to the executable...")
    pyinstaller_args.append("--add-data=BACKGR.png;.")

PyInstaller.__main__.run(pyinstaller_args)
