import os
import threading
import time
import tkinter as tk

import ttkbootstrap as tb
import vlc
from ttkbootstrap.constants import *

from utils import AnimeLibrary


class AnimeLibraryApp(tb.Window):
    def __init__(self, anime_dir: str):
        super().__init__(themename="cyborg")
        self.title("Anime Library Manager")
        self.geometry("800x600")

        self.is_fullscreen = False
        self.saved_geometry = None  # to restore window size after fullscreen

        # Keybindings for playback control
        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())
        self.bind("<space>", lambda e: self.pause_resume())  # pause/resume
        self.bind("<period>", lambda e: self.increase_speed())  # '.' = faster
        self.bind("<comma>", lambda e: self.decrease_speed())  # ',' = slower
        self.bind("<r>", lambda e: self.reset_speed())  # 'r' = reset speed
        self.bind("<Right>", lambda e: self.skip_seconds(10))  # → skip forward
        self.bind("<Left>", lambda e: self.skip_seconds(-10))  # ← skip backward
        self.bind_all(
            "<KeyPress-f>", lambda e: self.toggle_fullscreen()
        )  # toggle fullscreen
        self.bind_all(
            "<Escape>",
            lambda e: self.toggle_fullscreen() if self.is_fullscreen else None,
        )  # exit fullscreen

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

        # Video frame
        self.video_frame = tb.Frame(self.right_frame)
        self.video_frame.pack(fill=BOTH, expand=True, pady=10)
        self.video_frame.update_idletasks()

        # Control bar (bottom of right frame)
        controls = tb.Frame(self.right_frame)
        controls.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        btn_full = tb.Button(
            controls, text="Fullscreen", command=self.toggle_fullscreen
        )
        btn_full.pack(side=tk.RIGHT, padx=5)

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
            self.episode_list_var.set(episodes)
            # Bind double-click to play
            self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)
        except Exception as e:
            print(f"Error loading episodes for {anime_name}: {str(e)}")
            # Show error message to the user
            self.show_error_message(f"Failed to load episodes: {str(e)}")

    def toggle_fullscreen(self):
        """Toggle Tkinter fullscreen + video expansion"""
        if self.is_fullscreen:
            # Exit fullscreen
            self.attributes("-fullscreen", False)
            if self.saved_geometry:
                self.geometry(self.saved_geometry)
            self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            self.is_fullscreen = False
            print("Exited fullscreen")
        else:
            # Enter fullscreen
            self.saved_geometry = self.geometry()
            self.attributes("-fullscreen", True)
            self.left_frame.pack_forget()  # hide anime list
            self.right_frame.pack(fill=BOTH, expand=True)  # video takes full window
            self.is_fullscreen = True
            print("Entered fullscreen")

    def show_error_message(self, message):
        """Show an error message to the user"""
        error_dialog = tk.Toplevel(self.master)
        error_dialog.title("Error")
        label = tb.Label(error_dialog, text=message)
        label.pack(padx=10, pady=10)
        button = tb.Button(error_dialog, text="OK", command=error_dialog.destroy)
        button.pack(pady=5)

    def on_episode_double_click(self, event):
        """Triggered when an episode is double-clicked"""
        selection = self.episode_listbox.curselection()
        if not selection:
            return

        self.current_episode_index = selection[0]
        self.play_episode(self.current_episode_index)

    def play_episode(self, start_index: int):
        """Play the selected episode and continue playlist automatically"""
        # 🧹 Stop any currently playing media first
        if hasattr(self, "player") and self.player:
            try:
                self.player.stop()
            except Exception:
                pass

        def _play_thread():
            instance = vlc.Instance("--no-xlib")  # 👈 enable native VLC UI controls
            player = instance.media_player_new()
            self.player = player  # store reference so we can control it later

            # Embed the video output into Tkinter frame
            if os.name == "posix":  # Linux (X11)
                player.set_xwindow(
                    self.winfo_id()
                )  # use main window id for fullscreen compatibility
            elif os.name == "nt":  # Windows
                player.set_hwnd(self.video_frame.winfo_id())

            # Allow fullscreen toggle
            player.toggle_fullscreen()  # Optional: start in fullscreen if you want

            for i in range(start_index, len(self.current_episodes)):
                episode_file = self.current_episodes[i]
                full_path = os.path.join(self.current_anime_path, episode_file)
                media = instance.media_new(full_path)
                player.set_media(media)
                player.play()
                time.sleep(0.1)

                # Monitor playback
                while True:
                    state = player.get_state()
                    if state == vlc.State.Ended:
                        print("Episode ended, loading next...")
                        break
                    elif state in [vlc.State.Stopped, vlc.State.Error]:
                        break
                    time.sleep(0.5)

        threading.Thread(target=_play_thread, daemon=True).start()

    def set_playback_speed(self, rate: float):
        """Set the speed of current playback (e.g., 1.5x, 2x)"""
        if hasattr(self, "player") and self.player:  # type: ignore
            self.player.set_rate(rate)  # type: ignore

    def pause_resume(self):
        """Toggle pause/resume"""
        if hasattr(self, "player") and self.player:  # type: ignore
            self.player.pause()  # type: ignore

    def on_close(self):
        if hasattr(self, "player"):
            self.player.stop()
        self.destroy()

    def increase_speed(self):
        """Increase playback speed by +0.25x"""
        if hasattr(self, "player") and self.player:
            rate = self.player.get_rate()
            new_rate = min(rate + 0.25, 4.0)
            self.player.set_rate(new_rate)
            print(f"Playback speed: {new_rate}x")

    def decrease_speed(self):
        """Decrease playback speed by -0.25x"""
        if hasattr(self, "player") and self.player:
            rate = self.player.get_rate()
            new_rate = max(rate - 0.25, 0.25)
            self.player.set_rate(new_rate)
            print(f"Playback speed: {new_rate}x")

    def reset_speed(self):
        """Reset playback speed to normal"""
        if hasattr(self, "player") and self.player:
            self.player.set_rate(1.0)
            print("Playback speed: 1.0x")

    def skip_seconds(self, seconds: int):
        """Skip forward or backward in the video"""
        if hasattr(self, "player") and self.player:
            time_pos = self.player.get_time()  # in ms
            new_time = max(time_pos + (seconds * 1000), 0)
            self.player.set_time(int(new_time))
            print(f"Skipped {seconds} seconds")

    def stop_video(self):
        """Stop and release the current VLC player"""
        if hasattr(self, "player") and self.player:
            try:
                self.player.stop()  # stop playback
                self.player.release()  # free VLC resources
                self.player = None  # clear reference
                print("VLC player closed")
            except Exception as e:
                print(f"Failed to close VLC player: {e}")


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    app = AnimeLibraryApp(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
