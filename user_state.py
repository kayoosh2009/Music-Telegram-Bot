import os
import json

DATA_DIR = "data"
USER_STATE_FILE = os.path.join(DATA_DIR, "user_state.json")

def _load_all():
    try:
        with open(USER_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def _save_all(data):
    try:
        with open(USER_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[user_state._save_all] {e}")

def get_user_state(user_id):
    """
    Returns dict with keys: genre (str or None), played (list of song ids), last_song_id (int or None),
    awaiting_add_song_id (optional)
    """
    data = _load_all()
    key = str(user_id)
    state = data.get(key)
    if not isinstance(state, dict):
        state = {"genre": None, "played": [], "last_song_id": None}
        data[key] = state
        _save_all(data)
    # normalization
    if "genre" not in state: state["genre"] = None
    if "played" not in state or not isinstance(state["played"], list): state["played"] = []
    if "last_song_id" not in state: state["last_song_id"] = None
    return state

def save_user_state(user_id, state):
    if not isinstance(state, dict):
        raise ValueError("state must be dict")
    data = _load_all()
    data[str(user_id)] = state
    _save_all(data)

def reset_played(user_id):
    s = get_user_state(user_id)
    s["played"] = []
    save_user_state(user_id, s)
