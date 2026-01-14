from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore


def _ensure_firebase_initialized() -> None:
  try:
    firebase_admin.get_app()
    return
  except ValueError:
    pass

  service_account_path = Path(__file__).resolve().parents[1] / "serviceAccount.json"
  cred = credentials.Certificate(str(service_account_path))
  firebase_admin.initialize_app(cred)


_ensure_firebase_initialized()

app = firebase_admin.get_app()
db = firestore.client()
