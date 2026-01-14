import inspect
from typing import Any

from fastapi import FastAPI, Request

import db.firebase  # Ensures Firebase Admin SDK is initialized
from db.helpers import verify_firebase_auth_header
from db.firebase import db

app = FastAPI()


@app.get("/")
async def read_root():
  return {"Hello": "World"}


@app.post("/kyc")
async def kyc_verification(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  uid = user["uid"]
  db.collection("users").document(uid).set({"kyc": True}, merge=True)

  return {"uid": uid, "kyc": True, "status": "KYC verified"}


@app.post("/generate-id")
async def generate_id(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  return {
    "message": "In development"
  }


@app.get("/get-ids")
async def get_ids(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))

  snapshot_or_awaitable = db.collection("users").document(user["uid"]).get()
  user_doc: Any = await snapshot_or_awaitable if inspect.isawaitable(snapshot_or_awaitable) else snapshot_or_awaitable

  if not user_doc.exists:
    return {"success": True, "ids": {}}

  data = user_doc.to_dict() or {}
  ids = data.get("ids") or {}
  if not isinstance(ids, dict):
    ids = {}

  return {"success": True, "ids": ids}
