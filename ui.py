# ui.py
import os
import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from library import AnimeLibrary
from player import CelluloidPlayer
from watch_data import load_watch_data


class AnimeLibraryUI(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("800x600")

        self.library = AnimeLibrary(anime_dir)
        self.anime_list = []  # tuples: (name, path)
        self.current_anime_path = ""
        self.current_episodes = []

        self.selected_anime_index = tk.IntVar()
        self.episode_list_var = tk.StringVar(value=[])

        # Frames
        self.left_frame = tb.Frame(self, padding=10)
        self.left_frame.pack(side=LEFT, fill=Y)

        self.right_frame = tb.Frame(self, padding=10)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Anime listbox
        self.anime_listbox = tk.Listbox(
            self.left_frame, height=30, width=50, selectmode=tk.SINGLE
        )
        self.anime_listbox.pack(fill=Y, expand=True)
        self.anime_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        # Episode listbox
        self.episode_listbox = tk.Listbox(
            self.right_frame, listvariable=self.episode_list_var, height=30
        )
        self.episode_listbox.pack(fill=BOTH, expand=True)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        # Video frame
        self.video_frame = tb.Frame(self.right_frame)
        self.video_frame.pack(fill=BOTH, expand=True, pady=10)
        self.player = CelluloidPlayer()

        self.load_anime_list()
        self.load_last_watched()

    def load_anime_list(self):
        self.anime_list = self.library.list_all_animes()
        self.anime_listbox.delete(0, "end")
        for name, _ in self.anime_list:
            self.anime_listbox.insert("end", name)

    def on_anime_select(self, event):
        selection = self.anime_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        name, path = self.anime_list[index]
        self.current_anime_path = path
        self.current_episodes = self.library.list_episode_files(path)
        self.episode_list_var.set(self.current_episodes)

    def on_episode_double_click(self, event):
        selection = self.episode_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        # full paths of all remaining episodes
        playlist = [os.path.join(self.current_anime_path, ep) for ep in self.current_episodes]
        self.player.play_playlist(playlist, start_index=index)

    def load_last_watched(self):
        episode, pos = load_watch_data()
        if episode:
            print(f"[UI] Resuming last watched: {episode} at {pos}ms")
            # self.player.play_episode(episode, pos)

    def on_close(self):
        self.player.stop()
        self.destroy()
