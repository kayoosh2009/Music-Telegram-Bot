import firebase_admin
from firebase_admin import credentials, storage, firestore
from config import FIREBASE_CREDENTIALS, FIREBASE_STORAGE_BUCKET
import pathlib

# ---------------------------
# Инициализация Firebase
# ---------------------------
try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_app = firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_STORAGE_BUCKET
    })
except Exception as e:
    print("Firebase init error:", e)
    raise e

db = firestore.client()
bucket = storage.bucket()

# ---------------------------
# Функции для работы с Firebase
# ---------------------------
def upload_file_to_storage(local_path: str, dest_name: str) -> str:
    """Загружает файл в Firebase Storage и возвращает публичный URL"""
    blob = bucket.blob(dest_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

def save_track_metadata(metadata: dict) -> str:
    """Сохраняет данные трека в Firestore и возвращает ID документа"""
    doc_ref = db.collection("tracks").add(metadata)
    return doc_ref[1].id  # возвращаем ID документа

