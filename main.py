from blockchain import register_tourist
from db.firebase import db as firestore_db
from db.helpers import verify_firebase_auth_header
from eth_account import Account
from pydantic import AnyUrl, BaseModel, Field
from fastapi import FastAPI, Request
import inspect
from typing import Any
from datetime import datetime, timedelta

from ai.feature_eng import extract_features
from ai.anomly_detector import detect_anomaly
from ai.rule_engine import apply_rules

from sms import send_sms

try:
  from dotenv import load_dotenv

  load_dotenv()
except Exception:
  pass

# line break


app = FastAPI()

class GPSPoint(BaseModel):
    lat: float
    lon: float
    timestamp: datetime

class MovementRequest(BaseModel):
    prev_point: GPSPoint
    curr_point: GPSPoint
    zone_risk: int
    deviation: int



async def _maybe_await(value: Any) -> Any:
  return await value if inspect.isawaitable(value) else value


class GenerateIDBody(BaseModel):
  expiry: int


class SendSmsBody(BaseModel):
  to: str = Field(min_length=4, description="E.164 format, e.g. +918603128570")
  message: str = Field(min_length=1, max_length=1000)


@app.get("/")
async def read_root():
  return {"Hello": "World"}


@app.post("/kyc")
async def kyc_verification(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  uid = user["uid"]
  await _maybe_await(firestore_db.collection("users").document(uid).set({"kyc": True}, merge=True))

  to_put_data = {
    "kyc": True
  }

  user_data = await _maybe_await(firestore_db.collection("users").document(user["uid"]).get())
  if user_data.exists:
    if not (user_data.to_dict() or {}).get("blockchain_account"):
      account = Account.create()
      to_put_data["blockchain_account"] = {  # type: ignore
        "address": account.address,
        "private_key": account.key.hex()
      }

  await _maybe_await(
    firestore_db.collection("users").document(uid).set(
      to_put_data,
      merge=True,
    )
  )

  return {"uid": uid, "kyc": True, "status": "KYC verified"}


@app.get("/kyc-status")
async def kyc_status(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  user_doc: Any = await _maybe_await(firestore_db.collection("users").document(user["uid"]).get())

  if not user_doc.exists:
    return {"kyc": False}

  data = user_doc.to_dict() or {}
  kyc_status = data.get("kyc") or False

  return {"kyc": kyc_status}


@app.post("/generate-id")
async def generate_id(body: GenerateIDBody, request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  user_doc: Any = await _maybe_await(firestore_db.collection("users").document(user["uid"]).get())

  user_doc_data = user_doc.to_dict() or {}
  kyc_status = user_doc_data.get("kyc") or False

  if not kyc_status:
    return {"error": "KYC not completed"}

  # if not user_doc_data.get("blockchain_account"):
  #   return {"error": "User does not exist. Please create user first."}

  # wallet_address = user_doc_data["blockchain_account"]["address"]
  user_uid = user["uid"]
  expiry = body.expiry

  contract = register_tourist(user_uid, expiry)
  hash_id = contract['contract']

  ids = user_doc_data.get("ids") or {}

  ids[hash_id] = {
    "expiry": body.expiry
  }

  await _maybe_await(
    firestore_db.collection("users").document(user["uid"]).set(
      {
        "ids": ids
      },
      merge=True,
    )
  )

  return {
    "hash_id": hash_id,
    "expiry": body.expiry,
    "message": "ID generated successfully",
  }


@app.get("/get-ids")
async def get_ids(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))

  user_doc: Any = await _maybe_await(firestore_db.collection("users").document(user["uid"]).get())

  if not user_doc.exists:
    return {"success": True, "ids": {}}

  data = user_doc.to_dict() or {}
  ids = data.get("ids") or {}
  if not isinstance(ids, dict):
    ids = {}

  return {"success": True, "ids": ids}

@app.post("/analyze-movement")
def analyze_movement(data: MovementRequest):

    features = extract_features(
        data.prev_point.dict(),
        data.curr_point.dict(),
        data.zone_risk,
        data.deviation
    )

    anomaly = detect_anomaly(features)
    alert = apply_rules(anomaly, features)

    if alert:
        return {
            "status": "ALERT",
            "data": alert
        }

    return {
        "status": "NORMAL",
        "data": None
    }


@app.post("/send-sms")
async def send_sms_endpoint(body: SendSmsBody, request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  to = body.to.strip()
  if not to.startswith("+"):
    return {"error": "'to' must be E.164 format starting with '+'"}

  try:
    resp = send_sms(to=to, text=body.message)
  except Exception as exc:
    # Avoid leaking credentials/config; return a simple error.
    return {"success": False, "error": str(exc)}

  messages = getattr(resp, "messages", None)
  if not messages:
    return {"success": False, "error": "No messages returned from Vonage", "raw": str(resp)}

  m0 = messages[0]
  status = getattr(m0, "status", None)
  message_id = getattr(m0, "message_id", None)

  return {
    "success": status == "0",
    "status": status,
    "message_id": message_id,
    "to": getattr(m0, "to", None) or to,
  }
