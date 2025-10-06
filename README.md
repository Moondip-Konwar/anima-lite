# Anima Lite

**Anima Lite** is a lightweight, simplified version of the original **Anima** project. While **Anima** is a full-fledged local anime library manager built using Tauri and Svelte, **Anima Lite** focuses on providing a more minimal, Python-based solution for organizing and managing anime collections.

For the full-featured version, check out the [Anima project](https://github.com/Moondip-Konwar/Anima).

## Features

- Browse through a grid of anime covers
- View episodes list for selected anime
- Resume watching from the last played episode
- Offline support for downloading anime covers

## Requirements

- Python 3.7+
- `tkinter` for GUI
- `ttkbootstrap` for styling
- `Pillow` for image processing
- `requests` for network operations
- `os` for interacting with the operating system (file paths, environment variables)
- `json` for reading/writing JSON data
- `re` for regular expressions
- `typing` for type hinting (e.g., `TypedDict`)
- `subprocess` for running external processes
- `signal` for handling OS signals (like process termination)
- `threading` for multithreading
- `PIL.ImageTk` for converting images to be used in `tkinter`
- **Celluloid** (for video playback) - This is **not** a Python package, but rather a command-line tool. You can install it on your system by following the instructions at [Celluloid GitHub](https://github.com/xt8/Celluloid) or using your package manager (e.g., `apt install celluloid` on Linux).

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/anime-library.git
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install **Celluloid**:
   - This application relies on the **Celluloid** video player, which must be installed on your system. Celluloid is not available as a Python package, so please install it through your system's package manager:
     - On Ubuntu/Debian:

       ```bash
       sudo apt install celluloid
       ```

     - On Fedora:

       ```bash
       sudo dnf install celluloid
       ```

     - On MacOS (via Homebrew):

       ```bash
       brew install celluloid
       ```

4. Set up environment variables:
   - Modify the `CACHE_DIR` and `VIDEOS_DIR` directly in the Python files (`main.py` and others):

     ```python
     VIDEOS_DIR = "/path/to/videos"
     CACHE_DIR = "/path/to/cache"
     ```

   - These values will be used to manage where the anime videos and cached covers are stored. (Note: A future update will allow configuring these paths more easily).

## Usage

1. Run the application:

   ```bash
   python anime_library.py
   ```

2. Browse through anime covers in the grid.

3. Select an anime to view its episode list.

4. Double-click on an episode to start playing.

5. Use the "Resume Last Watched" button to continue from where you left off.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
