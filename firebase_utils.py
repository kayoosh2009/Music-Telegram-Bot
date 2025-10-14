import os
import json
import pathlib
from typing import Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, storage

from config import FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_STORAGE_BUCKET, TMP_DOWNLOAD_DIR

# Ensure TMP dir exists
pathlib.Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Write service account JSON to temp file (if provided)
_sa_path = "/tmp/firebase_sa.json"
if FIREBASE_SERVICE_ACCOUNT_JSON:
    with open(_sa_path, "w") as f:
        f.write(FIREBASE_SERVICE_ACCOUNT_JSON)

# Initialize Firebase
try:
    cred = credentials.Certificate(_sa_path)
    default_app = firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})
    _db = firestore.client()
    _bucket = storage.bucket()
except Exception as e:
    print("Firebase init error:", e)
    _db = None
    _bucket = None

def upload_file_to_storage(local_path: str, dest_blob_name: str) -> str:
    """Upload local file to Firebase Storage and return public URL if possible."""
    if not _bucket:
        raise RuntimeError("Firebase Storage not initialized.")
    blob = _bucket.blob(dest_blob_name)
    blob.upload_from_filename(local_path)
    try:
        blob.make_public()
        return blob.public_url
    except Exception:
        return f"gs://{_bucket.name}/{dest_blob_name}"

def save_track_metadata(metadata: Dict[str, Any]) -> str:
    """Save metadata in Firestore and return doc id."""
    if not _db:
        raise RuntimeError("Firestore not initialized.")
    doc_ref = _db.collection("tracks").document()
    doc_ref.set({**metadata})
    return doc_ref.id

def get_tracks_by_genre(genre: str):
    if not _db:
        return []
    docs = _db.collection("tracks").where("genre", "==", genre).stream()
    return [{"id": d.id, **(d.to_dict() or {})} for d in docs]

def get_track_by_id(doc_id: str):
    if not _db:
        return None
    d = _db.collection("tracks").document(doc_id).get()
    if d.exists:
        return {"id": d.id, **d.to_dict()}
    return None

def add_favorite(user_id: int, track_id: str):
    if not _db:
        return
    ref = _db.collection("users").document(str(user_id)).collection("favorites").document(track_id)
    ref.set({"track_id": track_id})

def list_favorites(user_id: int):
    if not _db:
        return []
    docs = _db.collection("users").document(str(user_id)).collection("favorites").stream()
    return [d.id for d in docs]

def save_user_session(user_id: int, session_data: Dict[str, Any]):
    if not _db:
        return
    _db.collection("sessions").document(str(user_id)).set(session_data)

def load_user_session(user_id: int):
    if not _db:
        return {}
    d = _db.collection("sessions").document(str(user_id)).get()
    if d.exists:
        return d.to_dict()
    return {}

def init_user_messages_list(user_id: int):
    if not _db:
        return
    _db.collection("user_messages").document(str(user_id)).set({"msgs": []})

def append_user_message_id(user_id: int, message_id: int):
    if not _db:
        return
    _db.collection("user_messages").document(str(user_id)).update({"msgs": firestore.ArrayUnion([message_id])})

def get_user_message_ids(user_id: int):
    if not _db:
        return []
    d = _db.collection("user_messages").document(str(user_id)).get()
    if d.exists:
        return d.to_dict().get("msgs", [])
    return []

def clear_user_message_ids(user_id: int):
    if not _db:
        return
    _db.collection("user_messages").document(str(user_id)).delete()
