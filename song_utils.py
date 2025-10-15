import json
import os

SONG_FILE = "songs.json"

def load_songs():
    if not os.path.exists(SONG_FILE):
        with open(SONG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    with open(SONG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_songs(songs):
    with open(SONG_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

def add_song(song_id, name, artist, genre, file_id):
    songs = load_songs()
    song = {
        "id": song_id,
        "name": name,
        "artist": artist,
        "genre": genre,
        "file_id": file_id
    }
    songs.append(song)
    save_songs(songs)
    return song

def get_songs_by_genre(genre):
    songs = load_songs()
    return [s for s in songs if s["genre"].lower() == genre.lower()]

def get_song_by_id(song_id):
    songs = load_songs()
    for s in songs:
        if s["id"] == song_id:
            return s
    return None
