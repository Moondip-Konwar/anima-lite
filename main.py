# main.py
from ui import AnimeLibraryUI

if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
