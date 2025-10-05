import os
from library import AnimeLibrary
from player import CelluloidPlayer
from watch_data import load_watch_data, save_watch_data


class AnimeManager:
    def __init__(self, anime_dir: str):
        self.library = AnimeLibrary(anime_dir)
        self.anime_list = self.library.list_all_animes()
        self.player = CelluloidPlayer()

        self.current_anime_name: str | None = None
        self.current_anime_path: str | None = None
        self.current_episodes: list[str] = []

    # ------------------- Selection ------------------- #
    def select_anime(self, anime_name: str, anime_path: str):
        self.current_anime_name = anime_name
        self.current_anime_path = anime_path
        self.current_episodes = self.library.list_episode_files(anime_path)

    # ------------------- Playback ------------------- #
    def play_from_index(self, start_index: int):
        if not self.current_anime_path or not self.current_episodes:
            return
        playlist = [os.path.join(self.current_anime_path, ep) for ep in self.current_episodes]
        self.player.play_playlist(self.current_anime_name, playlist, start_index=start_index)

    def resume_last_watched(self):
        if not self.current_anime_name:
            return None
        result = load_watch_data(self.current_anime_name)
        if not result:
            return None
        episode_path, _ = result
        episode_file = os.path.basename(episode_path)
        if episode_file not in self.current_episodes:
            return None
        index = self.current_episodes.index(episode_file)
        self.play_from_index(index)
        return episode_file, index
