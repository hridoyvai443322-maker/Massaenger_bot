import os
from flask import Flask, request
import requests
from google import genai

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secure_verify_token")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


@app.route("/webhook", methods=["GET"])
def verify_webhook():
  token = request.args.get("hub.verify_token")
  challenge = request.args.get("hub.challenge")
  if token == VERIFY_TOKEN:
    return challenge, 200
  return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def handle_messages():
  data = request.json
  if data.get("object") == "page":
    for entry in data.get("entry", []):
      for messaging_event in entry.get("messaging", []):
        sender_id = messaging_event.get("sender", {}).get("id")

        if messaging_event.get("message") and not messaging_event[
            "message"
        ].get("is_echo"):
          text = messaging_event["message"].get("text")
          if text:
            response_text = generate_ai_response(text)
            send_messenger_message(sender_id, response_text)

  return "EVENT_RECEIVED", 200


def generate_ai_response(user_text):
  try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_text,
    )
    return response.text
  except Exception as e:
    return "দুঃখিত, এই মুহূর্তে আমি উত্তর দিতে পারছি না।"


def send_messenger_message(recipient_id, message_text):
  url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
  payload = {
      "recipient": {"id": recipient_id},
      "message": {"text": message_text},
  }
  headers = {"Content-Type": "application/json"}
  requests.post(url, json=payload, headers=headers)


if __name__ == "__main__":
  app.run(port=5000, debug=True)
