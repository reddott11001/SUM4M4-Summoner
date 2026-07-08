# SUM4M4 Summoner

A sleek, neon-red themed URL opener and tab summoner built with Python and CustomTkinter. 

## Features
- **Auto-Format URL**: Automatically prepends `https://` if missing.
- **Bulk URL Summoning**: Open a massive amount of tabs (1k, 1m, etc.) with a single click.
- **Timer Delay**: Add a custom delay between each opened tab (e.g., `60s`, `1m`).
- **Auto-Close Tabs**: Automatically closes the opened tabs using `Ctrl+W` so your browser doesn't crash.
- **Custom Background**: Drop a file named `BACKGR.png` into the folder and the app will automatically adapt to its size and use it as the background.
- **Persistent Counter**: Tracks how many URLs you have summoned over time.

## Installation
You can either run the Python script directly or use the provided executable.

### Using the Executable (.exe)
1. Navigate to the `dist` folder.
2. Run `SUM4M4_Summoner.exe`.

### Running from source
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyautogui pillow
   ```
2. Run the script:
   ```bash
   python main.py
   ```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
**Copyright (c) 2026 Reddott11001**
