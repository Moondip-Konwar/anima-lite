# watch_data.py
def save_watch_data(episode: str, position_ms: int):
    """
    Save the current episode and playback position.
    For now, just a dummy function.
    """
    print(f"[SAVE] Episode: {episode}, Position: {position_ms}ms")
    # You can replace with JSON or DB saving later


def load_watch_data() -> tuple[str, int]:
    """
    Load the last watched episode and position.
    Returns: (episode_path, position_ms)
    """
    print("[LOAD] Returning dummy last watched episode")
    return "", 0  # Dummy values
