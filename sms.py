from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from vonage import Auth, Vonage
from vonage_sms import SmsMessage

load_dotenv()


def send_sms(*, to: str, text: str, sender: Optional[str] = None):
  to = to.strip()
  if not to.startswith("+"):
    raise ValueError(
      "VONAGE_TO must be in E.164 format (start with '+'), e.g. +918603128570"
    )

  api_key = os.getenv("VONAGE_API_KEY")
  api_secret = os.getenv("VONAGE_API_SECRET")
  if not api_key or not api_secret:
    raise RuntimeError(
      "Missing Vonage credentials. Set VONAGE_API_KEY and VONAGE_API_SECRET in .env"
    )

  auth = Auth(api_key=api_key, api_secret=api_secret)
  client = Vonage(auth=auth)

  callback = os.getenv("VONAGE_CALLBACK")
  status_report_req = os.getenv("VONAGE_STATUS_REPORT_REQ")
  status_report_req_bool = None
  if status_report_req is not None:
    status_report_req_bool = status_report_req.strip().lower() in {"1", "true", "yes"}

  message = SmsMessage(
    to=to,
    from_=sender or os.getenv("VONAGE_FROM", "Vonage APIs"),
    text=text,
    sig=None,
    client_ref=os.getenv("VONAGE_CLIENT_REF"),
    type=None,
    ttl=None,
    status_report_req=status_report_req_bool,
    callback=callback,
    message_class=None,
    protocol_id=None,
    account_ref=None,
    entity_id=None,
    content_id=None,
  )

  response = client.sms.send(message)
  return response


def _print_sms_response(resp) -> None:
  messages = getattr(resp, "messages", None)
  if not messages:
    print("Vonage response (no messages list):", resp)
    return

  for i, m in enumerate(messages):
    # vonage_sms.responses.MessageResponse doesn't currently expose error text,
    # so status is the primary signal here.
    print(
      f"message[{i}] status={getattr(m, 'status', None)} "
      f"message_id={getattr(m, 'message_id', None)} "
      f"to={getattr(m, 'to', None)} "
      f"remaining_balance={getattr(m, 'remaining_balance', None)} "
      f"message_price={getattr(m, 'message_price', None)}"
    )


if __name__ == "__main__":
  resp = send_sms(to="+918603128570", text="Kya be")

  _print_sms_response(resp)

  if getattr(resp, "messages", None) and resp.messages[0].status == "0":
    print("Message sent successfully.")
  else:
    status = None
    if getattr(resp, "messages", None):
      status = resp.messages[0].status
    print(f"Message failed. status={status} resp={resp}")
