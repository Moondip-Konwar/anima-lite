import os
import re
from typing import Literal, TypedDict


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
        """Scan all anime directories and print detected anime names."""
        anime_dirs = self.get_anime_directories()

        if not anime_dirs:
            print("No anime directories found.")
            return

        print("Detected anime directories and guessed names:\n")

        for folder in anime_dirs:
            folder_path = os.path.join(self.root_dir, folder)
            name_guess = self.get_anime_name(folder_path)
            print(f"{folder}: {name_guess or '(Name not detected)'}")


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    anime_lib = AnimeLibrary(VIDEOS_DIR)
    anime_lib.scan()
