from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


def verify_firebase_auth_header(authorization: Optional[str]) -> Dict[str, Any]:
  if not authorization:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization header",
    )

  parts = authorization.strip().split()
  if len(parts) != 2 or parts[0].lower() != "bearer":
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid Authorization header format. Expected: "Bearer <token>"',
    )

  token = parts[1].strip()
  if not token:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing bearer token",
    )

  try:
    # Local import so this helper can be imported even in contexts
    # where Firebase isn't configured yet.
    from firebase_admin import auth as firebase_auth

    decoded = firebase_auth.verify_id_token(token, check_revoked=True)
    uid = decoded.get("uid") or decoded.get("sub")
    if not uid:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid Firebase token: missing uid",
      )

    user_record = firebase_auth.get_user(uid)
  except HTTPException:
    raise
  except Exception as exc:
    exc_name = exc.__class__.__name__
    if exc_name in {"ExpiredIdTokenError", "InvalidIdTokenError", "RevokedIdTokenError"}:
      detail = "Invalid or expired Firebase token"
    elif exc_name in {"UserNotFoundError"}:
      detail = "Firebase user not found"
    else:
      detail = "Authorization failed"

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail) from exc

  return {
      "uid": user_record.uid,
      "email": user_record.email,
      "name": user_record.display_name,
      "picture": user_record.photo_url,
      "phone_number": user_record.phone_number,
      "disabled": user_record.disabled,
      "custom_claims": user_record.custom_claims or {},
      "token_claims": decoded,
  }
