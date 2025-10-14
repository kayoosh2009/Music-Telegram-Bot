# firebase_utils.py

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Получаем Firebase Service Account из переменной окружения
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not FIREBASE_SERVICE_ACCOUNT_JSON:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON is not set in environment variables")

try:
    FIREBASE_CREDENTIALS = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
except json.JSONDecodeError as e:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: " + str(e))

# Инициализация Firebase Admin
try:
    if not firebase_admin._apps:  # предотвращаем повторную инициализацию
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print("Firebase init error:", e)
    raise e


def init_user_messages_list(user_id: int):
    """
    Создает пустой список сообщений пользователя в Firebase, если его нет.
    """
    try:
        user_ref = db.collection("users").document(str(user_id))
        if not user_ref.get().exists:
            user_ref.set({"messages": []})
    except Exception as e:
        print(f"Error initializing messages list for user {user_id}: {e}")
        raise e
