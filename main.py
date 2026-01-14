import inspect
from typing import Any

from fastapi import FastAPI, Request
from pydantic import AnyUrl, BaseModel, Field
from eth_account import Account

import db.firebase  # Ensures Firebase Admin SDK is initialized
from db.helpers import verify_firebase_auth_header
from db.firebase import db

app = FastAPI()


async def _maybe_await(value: Any) -> Any:
  return await value if inspect.isawaitable(value) else value


class CreateUserBody(BaseModel):
  profile_photo: AnyUrl
  phone: str = Field(min_length=3, max_length=32)


@app.get("/")
async def read_root():
  return {"Hello": "World"}


@app.post("/kyc")
async def kyc_verification(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  # print(user)

  uid = user["uid"]
  await _maybe_await(db.collection("users").document(uid).set({"kyc": True}, merge=True))

  return {"uid": uid, "kyc": True, "status": "KYC verified"}


@app.post("/create-user")
async def create_user(body: CreateUserBody, request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  to_put_data = {
      "profile_photo": str(body.profile_photo),
      "phone": body.phone,
  }

  user_data = await _maybe_await(db.collection("users").document(user["uid"]).get())
  if user_data.exists:
    if not (user_data.to_dict() or {}).get("blockchain_account"):
      account = Account.create()
      to_put_data["blockchain_account"] = {  # type: ignore
          "address": account.address,
          "private_key": account.key.hex(),
      }

  uid = user["uid"]
  await _maybe_await(
    db.collection("users").document(uid).set(
      to_put_data,
      merge=True,
    )
  )

  return {"uid": uid, "status": "User created"}


@app.post("/generate-id")
async def generate_id(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  if not user:
    return {"error": "Unauthorized"}

  user_doc: Any = await _maybe_await(db.collection("users").document(user["uid"]).get())

  user_doc_data = user_doc.to_dict() or {}
  kyc_status = user_doc_data.get("kyc") or False

  if not kyc_status:
    return {"error": "KYC not completed"}

  # Hit the smart contract and generate a temp ID

  # hash_id = "temp_id_hash_12345"

  # Assuming i got the id hash here

  return {
    "message": "In development"
  }


@app.get("/get-ids")
async def get_ids(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))

  user_doc: Any = await _maybe_await(db.collection("users").document(user["uid"]).get())

  if not user_doc.exists:
    return {"success": True, "ids": {}}

  data = user_doc.to_dict() or {}
  ids = data.get("ids") or {}
  if not isinstance(ids, dict):
    ids = {}

  return {"success": True, "ids": ids}
