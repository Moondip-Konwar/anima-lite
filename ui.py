import os
import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from library import AnimeLibrary
from player import CelluloidPlayer
from watch_data import load_watch_data, save_watch_data


class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("800x600")

        # Initialize library
        self.library = AnimeLibrary(anime_dir)
        self.anime_list = self.library.list_all_animes()

        # Player
        self.player = CelluloidPlayer()

        # Current selection state
        self.current_anime_name: str | None = None
        self.current_anime_path: str | None = None
        self.current_episodes: list[str] = []

        # GUI Variables
        self.episode_list_var = tk.StringVar(value=[])

        # Setup frames
        self._setup_frames()

        # Populate anime list
        self.load_anime_list()

        # Keybindings for convenience
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    # ------------------- UI SETUP ------------------- #
    def _setup_frames(self):
        self.left_frame = tb.Frame(self, padding=10)
        self.left_frame.pack(side=LEFT, fill=Y)

        self.right_frame = tb.Frame(self, padding=10)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Anime listbox
        self.anime_listbox = tk.Listbox(
            self.left_frame,
            height=30,
            width=50,
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self.anime_listbox.pack(fill=Y, expand=True)
        self.anime_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        # Episode listbox with horizontal scrollbar
        scrollbar_x = tk.Scrollbar(self.right_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.episode_listbox = tk.Listbox(
            self.right_frame,
            listvariable=self.episode_list_var,
            height=30,
            xscrollcommand=scrollbar_x.set,
        )
        self.episode_listbox.pack(fill=BOTH, expand=True)
        scrollbar_x.config(command=self.episode_listbox.xview)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        # Control bar
        controls = tb.Frame(self.right_frame)
        controls.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        btn_resume = tb.Button(
            controls, text="Resume Last Watched", command=self.resume_last_watched
        )
        btn_resume.pack(side=tk.RIGHT, padx=5)

    # ------------------- LOAD LISTS ------------------- #
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

        # Highlight last watched episode if available
        result = load_watch_data(anime_name)
        if result:
            episode_path, _pos = result
            episode_file = os.path.basename(episode_path)  # <-- important
            if episode_file in self.current_episodes:
                ep_index = self.current_episodes.index(episode_file)
                self.episode_listbox.selection_clear(0, "end")
                self.episode_listbox.selection_set(ep_index)
                print(f"[UI] Continue watching: {episode_file}")

    # ------------------- PLAYBACK ------------------- #
    def on_episode_double_click(self, event):
        selection = self.episode_listbox.curselection()
        if not selection:
            return
        index = selection[0]

        # Build playlist from selected episode to last
        playlist = [
            os.path.join(self.current_anime_path, ep) for ep in self.current_episodes
        ]
        self.player.play_playlist(self.current_anime_name, playlist, start_index=index)

    def resume_last_watched(self):
        """Resume last watched episode for current anime"""
        if not self.current_anime_name:
            print("[UI] No anime selected yet!")
            return
        if not self.current_episodes:
            print("[UI] No episodes loaded!")
            return

        result = load_watch_data(self.current_anime_name)
        if not result:
            print("[UI] No last watched info found!")
            return

        episode_path, _pos = result
        episode_file = os.path.basename(episode_path)  # <-- compare filenames only

        if episode_file not in self.current_episodes:
            print(
                f"[UI] Last watched episode {episode_file} not found in episode list!"
            )
            return

        index = self.current_episodes.index(episode_file)
        playlist = [
            os.path.join(self.current_anime_path, ep) for ep in self.current_episodes
        ]

        print(f"[UI] Resuming {episode_file} from episode {index+1}")
        self.player.play_playlist(self.current_anime_name, playlist, start_index=index)

    def stop_video(self):
        """Stop current playback"""
        if self.player:
            self.player.stop()

    # ------------------- CLOSE HANDLING ------------------- #
    def on_close(self):
        self.stop_video()
        self.destroy()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
