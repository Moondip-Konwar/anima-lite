# app.py
import json
import os
import pathlib
import threading

import webview

from cover_downloader import CACHE_DIR, download_cover
from manager import AnimeManager
from watch_data import load_watch_data

HERE = pathlib.Path(__file__).parent.resolve()
UI_FILE = os.path.join(HERE, "ui.html")


class Api:
    """
    Exposed to JS via pywebview. Methods return data (JSON-serializable).
    """

    def __init__(self, anime_dir: str):
        self.manager = AnimeManager(anime_dir)
        self.skip_downloading_covers = False
        # Build initial anime list (name, path)
        # Note: manager.anime_list expected to be list of (name, path)
        # (copied from your previous code)
        self._reload_anime_list()

    def _reload_anime_list(self):
        self.anime_items = []
        for name, path in self.manager.anime_list:
            self.anime_items.append({"name": name, "path": path})

    # ----------------- Helpers ----------------- #
    def _local_cover_path(self, anime_name: str):
        filename = anime_name.replace(" ", "_") + ".jpg"
        return os.path.join(CACHE_DIR, filename)

    # --------------- Exposed API ---------------- #
    def get_anime_list(self):
        """
        Return list of anime metadata: [{name, path, cover}]
        This tries to use cached cover if available. It will attempt download
        cover only once; on first failure it will set skip flag and stop trying.
        """
        items = []
        for item in self.anime_items:
            name = item["name"]
            path = item["path"]
            cover = None
            local = self._local_cover_path(name)
            if os.path.exists(local):
                cover = f"file://{os.path.abspath(local)}"
            else:
                if not self.skip_downloading_covers:
                    try:
                        result = download_cover(name)
                        if result:
                            cover = f"file://{os.path.abspath(result)}"
                    except Exception as e:
                        # If the downloader fails (no network or AniList blocked),
                        # stop attempting downloads for this session to avoid freezes
                        print(f"[app] Cover download failed for {name}: {e}")
                        print("[app] Skipping downloads for all covers.")
                        self.skip_downloading_covers = True
                        cover = None
            items.append({"name": name, "path": path, "cover": cover})
        return items

    def select_anime(self, name: str, path: str):
        """
        Select anime in manager and return episodes plus last-watched highlight info.
        Does NOT auto-play (unlike manager.resume_last_watched which plays).
        Response:
        {
            "episodes": [ "E01.mkv", "E02.mkv", ... ],
            "last_watched": { "episode": "E03.mkv", "index": 2 } or null
        }
        """
        self.manager.select_anime(name, path)
        episodes = self.manager.current_episodes.copy()

        # Check watch data without invoking manager.resume_last_watched()
        last = load_watch_data(name)
        last_info = None
        if last:
            episode_path, _pos = last
            ep_file = os.path.basename(episode_path)
            if ep_file in episodes:
                idx = episodes.index(ep_file)
                last_info = {"episode": ep_file, "index": idx}

        return {"episodes": episodes, "last_watched": last_info}

    def play_index(self, index: int):
        """
        Ask manager to play from this index (this will call your player).
        Runs in separate thread to avoid blocking the UI thread.
        """

        def _play():
            try:
                self.manager.play_from_index(index)
            except Exception as e:
                print(f"[app] play_index error: {e}")

        threading.Thread(target=_play, daemon=True).start()
        return {"ok": True}

    def resume_last_watched_action(self):
        """
        Call manager.resume_last_watched() — this WILL start playback (keeps original behaviour).
        Return the last watched entry (or null).
        """

        def _resume():
            try:
                result = self.manager.resume_last_watched()
                print("[app] resume_last_watched returned:", result)
            except Exception as e:
                print(f"[app] resume error: {e}")

        threading.Thread(target=_resume, daemon=True).start()
        # Also return the last-watched info (non-blocking by reading file)
        # to allow UI to highlight immediately.
        if not self.manager.current_anime_name:
            return {"last_watched": None}
        last = load_watch_data(self.manager.current_anime_name)
        if not last:
            return {"last_watched": None}
        episode_path, _ = last
        ep_file = os.path.basename(episode_path)
        if ep_file in self.manager.current_episodes:
            idx = self.manager.current_episodes.index(ep_file)
            return {"last_watched": {"episode": ep_file, "index": idx}}
        return {"last_watched": None}


def start_ui(videos_dir: str):
    api = Api(videos_dir)
    window = webview.create_window(
        "Anima-lite (web)", UI_FILE, js_api=api, width=1200, height=700, resizable=True
    )
    webview.start(gui="qt")  # prefer qt webview where available


if __name__ == "__main__":
    # Change this as required
    VIDEOS_DIR = os.path.expanduser("~/Videos")
    start_ui(VIDEOS_DIR)
