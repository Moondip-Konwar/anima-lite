# player.py
import os
import signal
import subprocess
import threading
import time

from watch_data import save_watch_data


class CelluloidPlayer:
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.current_playlist: list[str] = []
        self.current_episode_index: int = 0
        self.is_playing = False
        self._monitor_thread: threading.Thread | None = None

    def play_playlist(self, episodes: list[str], start_index: int = 0):
        """
        Play episodes from start_index till the end using CLI Celluloid.
        """
        self.stop()  # stop any existing playback

        if not episodes:
            print("[WARN] No episodes to play")
            return

        # Filter only existing files
        episodes = [ep for ep in episodes if os.path.exists(ep)]
        if not episodes:
            print("[ERROR] None of the episodes exist")
            return

        self.current_playlist = episodes
        self.current_episode_index = start_index
        self.is_playing = True

        # CLI Celluloid supports multiple files as arguments
        playlist_to_play = episodes[start_index:]
        cmd = ["celluloid"] + playlist_to_play
        print(f"[Celluloid] Playing playlist: {playlist_to_play}")
        self.process = subprocess.Popen(cmd)

        # Monitor thread to detect when playback finishes
        self._monitor_thread = threading.Thread(
            target=self._monitor_process, daemon=True
        )
        self._monitor_thread.start()

    def _monitor_process(self):
        if self.process:
            self.process.wait()
            self.is_playing = False
            if self.current_playlist and self.current_episode_index < len(
                self.current_playlist
            ):
                last_episode = self.current_playlist[self.current_episode_index]
                save_watch_data(last_episode, 0)
                print(f"[Celluloid] Finished playlist starting from {last_episode}")

    def stop(self):
        if self.process:
            try:
                self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            self.process = None
            self.is_playing = False
            if self.current_playlist and self.current_episode_index < len(
                self.current_playlist
            ):
                last_episode = self.current_playlist[self.current_episode_index]
                save_watch_data(last_episode, 0)
                print(f"[Celluloid] Stopped playlist at {last_episode}")

    def pause_resume(self):
        print("[WARN] Pause/Resume not supported with CLI Celluloid")

    def skip_seconds(self, seconds: int):
        print("[WARN] Skipping not supported with CLI Celluloid")
