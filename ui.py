import os
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from library import AnimeLibrary
from player import CelluloidPlayer
from watch_data import load_watch_data, save_watch_data


class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("1000x650")
        self.minsize(900, 600)

        # ------------------- State ------------------- #
        self.library = AnimeLibrary(anime_dir)
        self.anime_list = self.library.list_all_animes()
        self.player = CelluloidPlayer()
        self.current_anime_name: str | None = None
        self.current_anime_path: str | None = None
        self.current_episodes: list[str] = []

        # ------------------- UI Variables ------------------- #
        self.episode_list_var = tk.StringVar(value=[])

        # ------------------- Layout ------------------- #
        self._setup_layout()
        self.load_anime_list()

        # Keybindings
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    # ------------------- Layout ------------------- #
    def _setup_layout(self):
        # Left panel: Anime list
        self.left_panel = tb.Frame(self, padding=10)
        self.left_panel.pack(side=LEFT, fill=Y)

        tb.Label(self.left_panel, text="Anime Library", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))
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

        # Right panel: Episodes + Controls
        self.right_panel = tb.Frame(self, padding=10)
        self.right_panel.pack(side=RIGHT, fill=BOTH, expand=True)

        # Episodes label
        tb.Label(self.right_panel, text="Episodes", font=("Segoe UI", 14, "bold")).pack(anchor=W, pady=(0, 5))

        # Episode listbox with scrollbar
        scrollbar_x = tk.Scrollbar(self.right_panel, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.episode_listbox = tk.Listbox(
            self.right_panel,
            listvariable=self.episode_list_var,
            height=25,
            font=("Segoe UI", 12),
            xscrollcommand=scrollbar_x.set,
        )
        self.episode_listbox.pack(fill=BOTH, expand=True)
        scrollbar_x.config(command=self.episode_listbox.xview)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        # Controls frame
        controls = tb.Frame(self.right_panel)
        controls.pack(side=BOTTOM, fill=X, pady=10)

        tb.Button(controls, text="Resume Last Watched", bootstyle="success", command=self.resume_last_watched).pack(side=RIGHT, padx=5)
        tb.Button(controls, text="Stop Video", bootstyle="danger", command=self.stop_video).pack(side=RIGHT, padx=5)

    # ------------------- Load Anime List ------------------- #
    def load_anime_list(self):
        self.anime_listbox.delete(0, "end")
        for name, _ in self.anime_list:
            self.anime_listbox.insert("end", name)

    def on_anime_select(self, event):
        selection = self.anime_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        anime_name, anime_path = self.anime_list[index]

        self.current_anime_name = anime_name
        self.current_anime_path = anime_path
        self.current_episodes = self.library.list_episode_files(anime_path)
        self.episode_list_var.set(self.current_episodes)

        # Highlight last watched episode if exists
        result = load_watch_data(anime_name)
        if result:
            episode_path, _pos = result
            episode_file = os.path.basename(episode_path)
            if episode_file in self.current_episodes:
                ep_index = self.current_episodes.index(episode_file)
                self.episode_listbox.selection_clear(0, "end")
                self.episode_listbox.selection_set(ep_index)
                self.episode_listbox.see(ep_index)  # Scroll to episode
                print(f"[UI] Continue watching: {episode_file}")

    # ------------------- Playback ------------------- #
    def on_episode_double_click(self, event):
        selection = self.episode_listbox.curselection()
        if not selection:
            return
        index = selection[0]

        playlist = [os.path.join(self.current_anime_path, ep) for ep in self.current_episodes]
        self.player.play_playlist(self.current_anime_name, playlist, start_index=index)

    def resume_last_watched(self):
        if not self.current_anime_name or not self.current_episodes:
            print("[UI] No anime selected or episodes loaded!")
            return

        result = load_watch_data(self.current_anime_name)
        if not result:
            print("[UI] No last watched info found!")
            return

        episode_path, _pos = result
        episode_file = os.path.basename(episode_path)

        if episode_file not in self.current_episodes:
            print(f"[UI] Last watched episode {episode_file} not found in episode list!")
            return

        index = self.current_episodes.index(episode_file)
        playlist = [os.path.join(self.current_anime_path, ep) for ep in self.current_episodes]

        print(f"[UI] Resuming {episode_file} from episode {index+1}")
        self.player.play_playlist(self.current_anime_name, playlist, start_index=index)
        self.episode_listbox.selection_clear(0, "end")
        self.episode_listbox.selection_set(index)
        self.episode_listbox.see(index)

    def stop_video(self):
        if self.player:
            self.player.stop()

    # ------------------- Close Handling ------------------- #
    def on_close(self):
        self.stop_video()
        self.destroy()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
