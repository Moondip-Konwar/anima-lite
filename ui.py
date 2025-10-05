import os
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from manager import AnimeManager


class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("900x600")

        # ------------------- Manager ------------------- #
        self.manager = AnimeManager(anime_dir)

        # ------------------- UI Variables ------------------- #
        self.episode_list_var = tk.StringVar(value=[])

        # ------------------- Layout ------------------- #
        self._setup_layout()

        # ------------------- Populate Anime List ------------------- #
        self.load_anime_list()

        # ------------------- Keybindings ------------------- #
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    # ------------------- Layout ------------------- #
    def _setup_layout(self):
        # Left Panel - Anime List
        self.left_panel = tb.Frame(self, padding=10)
        self.left_panel.pack(side=LEFT, fill=Y)

        self.anime_listbox = tk.Listbox(
            self.left_panel,
            height=35,
            width=40,
            selectmode=tk.SINGLE,
            exportselection=False,
            font=("Segoe UI", 12)
        )
        self.anime_listbox.pack(fill=Y, expand=True)
        self.anime_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        # Right Panel - Episodes
        self.right_panel = tb.Frame(self, padding=10)
        self.right_panel.pack(side=RIGHT, fill=BOTH, expand=True)

        scrollbar_x = tk.Scrollbar(self.right_panel, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.episode_listbox = tk.Listbox(
            self.right_panel,
            listvariable=self.episode_list_var,
            height=30,
            xscrollcommand=scrollbar_x.set,
            font=("Segoe UI", 12)
        )
        self.episode_listbox.pack(fill=BOTH, expand=True)
        scrollbar_x.config(command=self.episode_listbox.xview)

        # Bind double-click
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        # Control bar
        controls = tb.Frame(self.right_panel)
        controls.pack(side=tk.BOTTOM, fill=X, pady=5)
        self.btn_resume = tb.Button(
            controls, text="Resume Last Watched", command=self.resume_last_watched
        )
        self.btn_resume.pack(side=RIGHT, padx=5)

    # ------------------- Anime List ------------------- #
    def load_anime_list(self):
        self.anime_listbox.delete(0, "end")
        for name, _ in self.manager.anime_list:
            self.anime_listbox.insert("end", name)

    def on_anime_select(self, event):
        selection = self.anime_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        anime_name, anime_path = self.manager.anime_list[index]
        self.manager.select_anime(anime_name, anime_path)
        self.episode_list_var.set(self.manager.current_episodes)

        # Highlight last watched episode if available
        result = self.manager.resume_last_watched()
        if result:
            episode_file, _ = result
            ep_index = self.manager.current_episodes.index(episode_file)
            self.episode_listbox.selection_clear(0, "end")
            self.episode_listbox.selection_set(ep_index)
            print(f"[UI] Highlighting last watched: {episode_file}")

    # ------------------- Playback ------------------- #
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

    # ------------------- Close ------------------- #
    def on_close(self):
        self.stop_video()
        self.destroy()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
