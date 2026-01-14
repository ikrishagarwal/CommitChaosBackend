from email import message
from fastapi import FastAPI, Request

import db.firebase  # Ensures Firebase Admin SDK is initialized
from db.helpers import verify_firebase_auth_header
from db.firebase import db

app = FastAPI()


@app.get("/")
async def read_root():
  return {"Hello": "World"}


@app.post("/kyc")
async def kyc_verification(user_id: int, request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  print("Verified Firebase user:", user)

  uid = user["uid"]
  db.collection("users").document(uid).set({"kyc": True}, merge=True)

  return {"user_id": user_id, "uid": uid, "kyc": True, "status": "KYC verification initiated"}


@app.post("/generate-id")
async def generate_id(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  print("Verified Firebase user:", user)

  return {
    "message": "In development"
  }


@app.get("/get-ids")
async def status_check(request: Request):
  user = verify_firebase_auth_header(request.headers.get("Authorization"))
  print("Verified Firebase user:", user)

  return {
    "message": "In development"
  }
