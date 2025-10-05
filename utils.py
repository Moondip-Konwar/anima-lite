import json
import os
import re
from typing import TypedDict

from natsort import natsorted


def write_json(file_path: str, data: dict) -> None:
    """Write a dictionary to a JSON file. Create file if it doesn't exist."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def read_json(file_path: str) -> dict:
    """Read a JSON file and return a dictionary. Return empty dict if file doesn't exist."""
    if not os.path.isfile(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


class FileDirSplit(TypedDict):
    files: list[str]
    dirs: list[str]


class AnimeLibrary:
    """
    A utility class to detect and process anime directories by analyzing their episode file structures.
    """

    def __init__(self, root_dir: str) -> None:
        if not os.path.isdir(root_dir):
            raise ValueError(f"Invalid directory path: {root_dir}")

        self.root_dir = os.path.abspath(root_dir)
        os.chdir(self.root_dir)

        # Load anime metadata from JSON if exists, else empty dict
        self.json_file = os.path.join(self.root_dir, "anime_data.json")
        self.anime_data: dict[str, dict] = read_json(self.json_file)

    def save_anime_data(self) -> None:
        """Save current anime data to JSON file."""
        write_json(self.json_file, self.anime_data)

    @staticmethod
    def _split_files_and_dirs(items: list[str], base_path: str) -> FileDirSplit:
        """Separate file and directory names from a given list."""
        files: list[str] = []
        dirs: list[str] = []

        for name in items:
            full_path = os.path.join(base_path, name)
            (files if os.path.isfile(full_path) else dirs).append(name)

        return {"files": files, "dirs": dirs}

    def _is_anime_folder(self, folder_name: str) -> bool:
        """Determine if a given folder likely contains anime episodes."""
        full_path = os.path.join(self.root_dir, folder_name)
        if not os.path.isdir(full_path):
            return False

        contents = os.listdir(full_path)
        separated = self._split_files_and_dirs(contents, full_path)
        file_count = len(separated["files"])

        return file_count >= 10  # Arbitrary threshold, tweak as needed

    def get_anime_directories(self) -> list[str]:
        """Return a list of directories that appear to contain anime series."""
        all_items = os.listdir(self.root_dir)
        return [d for d in all_items if self._is_anime_folder(d)]

    @staticmethod
    def _clean_filename(name: str) -> str:
        """Clean a filename by removing extensions, tags, and common episode markers."""
        name = os.path.splitext(name)[0]  # remove extension
        name = re.sub(r"\[.*?\]", "", name)  # remove [bracketed tags]
        name = re.sub(r"[-_\.]", " ", name)  # normalize separators
        name = re.sub(r"\s+", " ", name).strip()

        # Remove episode numbers and variants
        name = re.sub(
            r"(episode|ep|e|s\d{1,2}e\d{1,2}|part)\s*\d+", "", name, flags=re.I
        )
        return name.strip(" -_")

    @staticmethod
    def _guess_anime_name_from_episodes(episode_files: list[str]) -> str:
        """Guess the anime name from cleaned episode filenames."""
        if not episode_files:
            return ""

        cleaned_names = [AnimeLibrary._clean_filename(ep) for ep in episode_files]

        # Start with first as base, then reduce to common prefix
        common_prefix = cleaned_names[0].split()

        for name in cleaned_names[1:]:
            words = name.split()
            # Compare word-by-word
            i = 0
            while (
                i < len(common_prefix)
                and i < len(words)
                and common_prefix[i].lower() == words[i].lower()
            ):
                i += 1
            common_prefix = common_prefix[:i]
            if not common_prefix:
                break

        return " ".join(common_prefix).strip(" -_")

    def get_anime_name(self, folder_path: str) -> str:
        """Infer the anime's name by comparing episode filenames in the folder."""
        if not os.path.isdir(folder_path):
            raise ValueError(f"Invalid anime directory path: {folder_path}")

        contents = os.listdir(folder_path)
        separated = self._split_files_and_dirs(contents, folder_path)
        episode_files = separated["files"]

        return self._guess_anime_name_from_episodes(episode_files)

    def scan(self) -> None:
        """
        Scan all anime directories, populate self.anime_data,
        and save to JSON automatically.
        """
        anime_dirs = self.get_anime_directories()

        if not anime_dirs:
            print("No anime directories found.")
            return

        print("Detected anime directories and guessed names:\n")

        for folder in anime_dirs:
            folder_path = os.path.join(self.root_dir, folder)
            name_guess = self.get_anime_name(folder_path)

            if name_guess:
                # Add or update the anime in internal data
                self.add_or_update_anime(name_guess, folder_path)
                print(f"{folder}: {name_guess}")
            else:
                print(f"{folder}: (Name not detected)")

        # Save any new/updated anime data to JSON
        self.save_anime_data()

    def get_episode_path(
        self, anime_folder_path: str, episode_number: int
    ) -> str | None:
        """
        Return the full path of an episode using natural sort.
        Returns None if episode_number is out of range.
        """
        if not os.path.isdir(anime_folder_path):
            return None

        files = self._split_files_and_dirs(
            os.listdir(anime_folder_path), anime_folder_path
        )["files"]
        sorted_files = natsorted(files)
        if 1 <= episode_number <= len(sorted_files):
            return os.path.join(anime_folder_path, sorted_files[episode_number - 1])
        return None

    def list_all_animes(self) -> list[tuple[str, str]]:
        """
        Return a list of all anime names and their folder paths.
        Uses self.anime_data if available, otherwise scans directories.
        """
        anime_list = []
        if self.anime_data:
            for name, info in self.anime_data.items():
                anime_list.append((name, info.get("path", "")))
        else:
            dirs = self.get_anime_directories()
            for folder in dirs:
                path = os.path.join(self.root_dir, folder)
                name = self.get_anime_name(path)
                anime_list.append((name, path))
                self.anime_data[name] = {"path": path}
            self.save_anime_data()
        return anime_list

    def list_episode_files(self, anime_folder_path: str) -> list[str]:
        """Return a naturally sorted list of episode files for a given anime folder."""
        if not os.path.isdir(anime_folder_path):
            return []
        files = self._split_files_and_dirs(
            os.listdir(anime_folder_path), anime_folder_path
        )["files"]
        return natsorted(files)

    def count_episodes(self, anime_folder_path: str) -> int:
        """Return the number of episodes in an anime folder."""
        return len(self.list_episode_files(anime_folder_path))

    def add_or_update_anime(self, anime_name: str, anime_folder_path: str) -> None:
        """Add a new anime to the internal data or update existing entry."""
        self.anime_data[anime_name] = {"path": anime_folder_path}
        self.save_anime_data()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    anime_lib = AnimeLibrary(VIDEOS_DIR)
    anime_lib.scan()
