import os
import tkinter as tk

import ttkbootstrap as tb
from PIL import Image, ImageTk
from requests.exceptions import RequestException
from ttkbootstrap.constants import *

from cover_downloader import CACHE_DIR, download_cover
from manager import AnimeManager

CARD_WIDTH = 150
CARD_HEIGHT = 200
CARDS_PER_ROW = 5


class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="darkly")
        self.title("Anime Library")
        self.geometry("1200x700")

        self.manager = AnimeManager(anime_dir)

        # Keep references to images to prevent garbage collection
        self.cover_images = {}

        self._setup_layout()
        self.load_anime_grid()

        # Keybindings
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    def _setup_layout(self):
        self.left_frame = tb.Frame(self, padding=10)
        self.left_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.right_frame = tb.Frame(self, padding=10)
        self.right_frame.pack(side=RIGHT, fill=Y)

        self.title_label = tb.Label(
            self.left_frame,
            text="Anime Library",
            font=("Segoe UI", 24, "bold"),
            padding=10,
        )
        self.title_label.pack(side=TOP, fill=X)

        self.canvas_frame = tb.Frame(self.left_frame)
        self.canvas_frame.pack(side=TOP, fill=BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", highlightthickness=0)
        self.scrollbar = tb.Scrollbar(
            self.canvas_frame, orient=VERTICAL, command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.grid_frame = tb.Frame(self.canvas, style="Card.TFrame")
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", self._on_frame_configure)

        # Right panel
        self.episode_label = tb.Label(
            self.right_frame, text="Episodes", font=("Segoe UI", 18, "bold")
        )
        self.episode_label.pack(side=TOP, pady=5)

        self.episode_listbox = tk.Listbox(
            self.right_frame,
            width=40,
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="white",
            selectbackground="#ff6600",
        )
        self.episode_listbox.pack(side=TOP, fill=BOTH, expand=True)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        self.btn_resume = tb.Button(
            self.right_frame,
            text="Resume Last Watched",
            bootstyle="warning",
            command=self.resume_last_watched,
        )
        self.btn_resume.pack(side=TOP, pady=10)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ------------------- Anime Grid ------------------- #

    def load_anime_grid(self):
        """Load anime cards into the scrollable grid with fixed image and title sizes."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        row = 0
        col = 0
        skip_downloading_covers: bool = False

        for anime_name, anime_path in self.manager.anime_list:
            # Parent card frame
            card_frame = tb.Frame(
                self.grid_frame,
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                padding=5,
                relief=RAISED,
                borderwidth=2,
                bootstyle="dark",
            )
            card_frame.grid(row=row, column=col, padx=10, pady=10)
            card_frame.grid_propagate(False)  # Prevent resizing

            # -------- Image Container --------
            image_frame = tb.Frame(card_frame, width=CARD_WIDTH, height=CARD_HEIGHT)
            image_frame.pack_propagate(False)
            image_frame.pack(side=TOP, fill=BOTH)

            # Determine cover path
            filename = anime_name.replace(" ", "_") + ".jpg"
            cover_path = os.path.join(CACHE_DIR, filename)

            # Download cover only if missing
            if not skip_downloading_covers and not os.path.exists(cover_path):
                try:
                    result = download_cover(anime_name)
                    if result:
                        cover_path = result
                except Exception:
                    print(f"[UI] Could not download cover for {anime_name} (offline?)")
                    print("Skipping downloading for all covers....")
                    skip_downloading_covers = True
                    cover_path = None

            # Load image or fallback
            if cover_path and os.path.exists(cover_path):
                try:
                    img = Image.open(cover_path).convert("RGB")
                    img = img.resize(
                        (CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS
                    )
                    photo = ImageTk.PhotoImage(img)
                    img_label = tb.Label(image_frame, image=photo)
                    img_label.image = photo
                    self.cover_images[anime_name] = photo
                except Exception as e:
                    print(f"[UI] Failed to load cover {cover_path}: {e}")
                    img_label = tb.Label(image_frame, text="🖼️", font=("Segoe UI", 48))
            else:
                img_label = tb.Label(image_frame, text="🖼️", font=("Segoe UI", 48))

            img_label.pack(fill=BOTH, expand=True)

            # -------- Title Container --------
            title_frame = tb.Frame(card_frame, width=CARD_WIDTH, height=40)
            title_frame.pack_propagate(False)  # Fix title height
            title_frame.pack(side=BOTTOM, fill=X)

            title_label = tb.Label(
                title_frame,
                text=anime_name,
                font=("Segoe UI", 12),
                wraplength=CARD_WIDTH,
                anchor="center",
                justify="center",
            )
            title_label.pack(fill=BOTH, expand=True)

            # -------- Click Bindings --------
            for widget_item in (card_frame, img_label, title_label):
                widget_item.bind(
                    "<Button-1>",
                    lambda e, n=anime_name, p=anime_path: self.select_anime(n, p),
                )

            # Increment grid position
            col += 1
            if col >= CARDS_PER_ROW:
                col = 0
                row += 1

    def select_anime(self, anime_name, anime_path):
        self.manager.select_anime(anime_name, anime_path)
        self.episode_listbox.delete(0, "end")
        for ep in self.manager.current_episodes:
            self.episode_listbox.insert("end", ep)

        # Highlight last watched episode
        result = self.manager.resume_last_watched()
        if result:
            episode_file, _ = result
            ep_index = self.manager.current_episodes.index(episode_file)
            self.episode_listbox.selection_clear(0, "end")
            self.episode_listbox.selection_set(ep_index)
            print(f"[UI] Highlighting last watched: {episode_file}")

    def on_episode_double_click(self, event):
        selection = self.episode_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.manager.play_from_index(index)

    def resume_last_watched(self):
        result = self.manager.resume_last_watched()
        if result:
            episode_file, index = result
            self.episode_listbox.selection_clear(0, "end")
            self.episode_listbox.selection_set(index)
            print(f"[UI] Resuming last watched: {episode_file}")
        else:
            print("[UI] No last watched info available!")

    def stop_video(self):
        self.manager.player.stop()

    def on_close(self):
        self.stop_video()
        self.destroy()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    os.makedirs(CACHE_DIR, exist_ok=True)
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
