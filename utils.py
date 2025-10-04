import os
from typing import Literal

videos: str = "/home/moondip/Videos"
os.chdir(videos)


def separate_files_and_dirs(
    files_and_dirs: list[str], parent_path: str
) -> dict[Literal["files", "dirs"], list[str]]:
    files: list[str] = []
    dirs: list[str] = []

    for val in files_and_dirs:
        if os.path.isfile(os.path.join(parent_path, val)):
            files.append(val)
        else:
            dirs.append(val)

    # Separated for the sake of pyright
    result: dict[Literal["files", "dirs"], list[str]] = {"files": files, "dirs": dirs}
    return result


def is_anime_dir(dir: str, animes_container_dir: str) -> bool:
    sub_dirs = os.listdir(dir)
    parent_path: str = os.path.join(animes_container_dir, dir)
    files_count: int = len(separate_files_and_dirs(sub_dirs, parent_path)["files"])

    if files_count < 10:
        return False
    else:
        return True


def get_anime_dirs(animes_container_dir: str) -> list[str]:
    anime_dirs: list[str] = []

    # Filter out non-anime dirs
    for dir in os.listdir():
        if is_anime_dir(dir, animes_container_dir):
            anime_dirs.append(dir)

    return anime_dirs


print(get_anime_dirs(videos))
