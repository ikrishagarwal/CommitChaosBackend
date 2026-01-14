import base64
import json
import os

try:
  from dotenv import load_dotenv

  load_dotenv()
except Exception:
  # Optional: if python-dotenv isn't installed or .env isn't present.
  pass

import firebase_admin
from firebase_admin import credentials, firestore


def _ensure_firebase_initialized() -> None:
  try:
    firebase_admin.get_app()
    return
  except ValueError:
    pass

  service_account_json = os.getenv("CREDS")

  if service_account_json:
    try:
      service_account_info = json.loads(service_account_json)
    except Exception as exc:
      raise RuntimeError("Invalid CREDS") from exc
    cred = credentials.Certificate(service_account_info)
  else:
    raise RuntimeError(
        "Firebase credentials not found. Set the CREDS environment variable."
    )

  firebase_admin.initialize_app(cred)


_ensure_firebase_initialized()

app = firebase_admin.get_app()
db = firestore.client()
