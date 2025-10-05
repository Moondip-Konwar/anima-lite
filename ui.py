import os
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from manager import AnimeManager

CARD_WIDTH = 150
CARD_HEIGHT = 200
CARDS_PER_ROW = 5

class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="darkly")  # Dark theme
        self.title("Anime Library")
        self.geometry("1200x700")

        # Manager
        self.manager = AnimeManager(anime_dir)

        # UI Variables
        self.selected_anime_frame = None

        # Layout
        self._setup_layout()

        # Populate Grid
        self.load_anime_grid()

        # Keybindings
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    def _setup_layout(self):
        # Main frames
        self.left_frame = tb.Frame(self, padding=10)
        self.left_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.right_frame = tb.Frame(self, padding=10)
        self.right_frame.pack(side=RIGHT, fill=Y)

        # Title
        self.title_label = tb.Label(self.left_frame, text="Anime Library", font=("Segoe UI", 24, "bold"), padding=10)
        self.title_label.pack(side=TOP, fill=X)

        # Scrollable Canvas for anime grid
        self.canvas_frame = tb.Frame(self.left_frame)
        self.canvas_frame.pack(side=TOP, fill=BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.grid_frame = tb.Frame(self.canvas, style="Card.TFrame")
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", self._on_frame_configure)

        # Right panel: episode list + resume/play button
        self.episode_label = tb.Label(self.right_frame, text="Episodes", font=("Segoe UI", 18, "bold"))
        self.episode_label.pack(side=TOP, pady=5)

        self.episode_listbox = tk.Listbox(self.right_frame, width=40, font=("Segoe UI", 12), bg="#1e1e1e", fg="white", selectbackground="#ff6600")
        self.episode_listbox.pack(side=TOP, fill=BOTH, expand=True)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        self.btn_resume = tb.Button(self.right_frame, text="Resume Last Watched", bootstyle="warning", command=self.resume_last_watched)
        self.btn_resume.pack(side=TOP, pady=10)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ------------------- Anime Grid ------------------- #
    def load_anime_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        row = 0
        col = 0

        for anime_name, anime_path in self.manager.anime_list:
            card_frame = tb.Frame(self.grid_frame, width=CARD_WIDTH, height=CARD_HEIGHT, padding=5, relief=RAISED, borderwidth=2, bootstyle="dark")
            card_frame.grid(row=row, column=col, padx=10, pady=10)
            card_frame.grid_propagate(False)

            img_label = tb.Label(card_frame, text="🖼️", font=("Segoe UI", 48))
            img_label.pack(side=TOP, expand=True, fill=BOTH)

            title_label = tb.Label(card_frame, text=anime_name, font=("Segoe UI", 12), wraplength=CARD_WIDTH)
            title_label.pack(side=BOTTOM, pady=5)

            # Click binding
            card_frame.bind("<Button-1>", lambda e, n=anime_name, p=anime_path: self.select_anime(n, p))
            img_label.bind("<Button-1>", lambda e, n=anime_name, p=anime_path: self.select_anime(n, p))
            title_label.bind("<Button-1>", lambda e, n=anime_name, p=anime_path: self.select_anime(n, p))

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
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
