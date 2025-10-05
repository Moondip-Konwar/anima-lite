import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from utils import AnimeLibrary  # your class from previous code


class AnimeLibraryApp(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cosmo")
        self.title("Anime Library Manager")
        self.geometry("800x600")

        # Load library
        self.library = AnimeLibrary(anime_dir)
        self.anime_list = []  # list of tuples (name, path)

        # GUI variables
        self.selected_anime_index = tk.IntVar()
        self.episode_list_var = tk.StringVar(value=[])

        # Setup frames
        self._setup_frames()
        # Populate anime list
        self.load_anime_list()

    def _setup_frames(self):
        """Create basic frames for anime list and episode list"""
        self.left_frame = tb.Frame(self, padding=10)
        self.left_frame.pack(side=LEFT, fill=Y)

        self.right_frame = tb.Frame(self, padding=10)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Anime listbox
        self.anime_listbox = tk.Listbox(
            self.left_frame,
            height=30,
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self.anime_listbox.pack(fill=Y, expand=True)
        self.anime_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        # Episode listbox
        self.episode_listbox = tk.Listbox(
            self.right_frame,
            listvariable=self.episode_list_var,
            height=30,
        )
        self.episode_listbox.pack(fill=BOTH, expand=True)

    def load_anime_list(self):
        """Load all animes into the listbox"""
        self.anime_list = self.library.list_all_animes()
        self.anime_listbox.delete(0, "end")
        for name, _ in self.anime_list:
            self.anime_listbox.insert("end", name)

    def on_anime_select(self, event):
        """Triggered when an anime is selected"""
        selection = self.anime_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        anime_name, anime_path = self.anime_list[index]

        # Load episodes for this anime
        episodes = self.library.list_episode_files(anime_path)
        self.episode_list_var.set(episodes)


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"  # replace with your path
    app = AnimeLibraryApp(VIDEOS_DIR)
    app.mainloop()
