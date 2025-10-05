import os
import threading
import time
import tkinter as tk

import ttkbootstrap as tb
import vlc
from ttkbootstrap.constants import *

from utils import AnimeLibrary  # your class from previous code


class AnimeLibraryApp(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("800x600")

        # Load library
        self.library = AnimeLibrary(anime_dir)
        self.anime_list = []  # list of tuples (name, path)

        # GUI variables
        self.selected_anime_index = tk.IntVar()
        self.episode_list_var = tk.StringVar(value=[])  # type: ignore

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
            width=50,
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self.anime_listbox.pack(fill=Y, expand=True)
        self.anime_listbox.bind("<<ListboxSelect>>", self.on_anime_select)

        # Episode listbox
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

    def load_anime_list(self):
        """Load all animes into the listbox"""
        self.anime_list = self.library.list_all_animes()
        self.anime_listbox.delete(0, "end")
        for name, _ in self.anime_list:
            self.anime_listbox.insert("end", name)

    def on_anime_select(self, event):
        """Triggered when an anime is selected"""
        try:
            selection = self.anime_listbox.curselection()
            if not selection:
                return

            index = selection[0]
            anime_name, anime_path = self.anime_list[index]

            # Load episodes for this anime
            episodes = self.library.list_episode_files(anime_path)
            self.current_anime_path = anime_path
            self.current_episodes = episodes  # store for playlist
            self.current_episode_index = 0  # reset playlist pointer

            # Set episode list in UI
            self.episode_list_var.set(episodes)  # type: ignore

            # Bind double-click to play
            self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)
        except Exception as e:
            print(f"Error loading episodes for {anime_name}: {str(e)}")

    def on_episode_double_click(self, event):
        """Triggered when an episode is double-clicked"""
        selection = self.episode_listbox.curselection()
        if not selection:
            return

        self.current_episode_index = selection[0]
        self.play_episode(self.current_episode_index)

    def play_episode(self, start_index: int):
        """Play the selected episode and continue playlist automatically"""
        if not hasattr(self, "current_episodes"):
            return

        def _play_thread():
            instance = vlc.Instance()
            player = instance.media_player_new()

            for i in range(start_index, len(self.current_episodes)):
                episode_file = self.current_episodes[i]
                full_path = os.path.join(self.current_anime_path, episode_file)

                media = instance.media_new(full_path)
                player.set_media(media)

                # Optional: Enable subtitles automatically
                player.video_set_spu(-1)  # -1 = default track if available

                player.play()
                time.sleep(0.1)  # small delay to let VLC start

                # Monitor playback
                while True:
                    state = player.get_state()
                    # Save progress: episode index + current time
                    self.current_playback_position = player.get_time() / 1000  # seconds

                    if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
                        break
                    time.sleep(0.5)

        # Run playback in separate thread so UI remains responsive
        threading.Thread(target=_play_thread, daemon=True).start()

    def set_playback_speed(self, rate: float):
        """Set the speed of current playback (e.g., 1.5x, 2x)"""
        if hasattr(self, "player") and self.player:
            self.player.set_rate(rate)

    def pause_resume(self):
        """Toggle pause/resume"""
        if hasattr(self, "player") and self.player:
            self.player.pause()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"  # replace with your path
    app = AnimeLibraryApp(VIDEOS_DIR)
    app.mainloop()
