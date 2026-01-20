#!/usr/bin/env python3
import os
import asyncio
import threading
from flask import Flask, request, render_template_string, redirect
from telethon import TelegramClient, events
import openai

# ================= BASIC CONFIG =================
BASE_DIR = "kaalix_data"
SESS_DIR = f"{BASE_DIR}/sessions"
os.makedirs(SESS_DIR, exist_ok=True)

PORT = int(os.environ.get("PORT", 8080))

accounts = {}   # phone -> info
clients = {}    # phone -> TelegramClient
openai.api_key = ""

# ================= HTML PANEL =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>KAALIX CONTROL PANEL</title>
<style>
body{background:#0b0e14;color:#eaeaea;font-family:Arial}
.box{background:#111;padding:20px;margin:20px;border-radius:10px}
input,textarea,button{width:100%;padding:8px;margin:6px 0}
button{background:#4caf50;border:none;font-weight:bold}
.stop{background:#f44336}
pre{background:#000;padding:10px;white-space:pre-wrap}
small{color:#aaa}
</style>
</head>
<body>

<div class="box">
<h2>🔑 OpenAI API Key</h2>
<form method="post" action="/set_ai">
<input name="key" placeholder="sk-xxxxxxxxxxxxxxxx" required>
<button>Save Key</button>
</form>
<small>Key server memory me rahegi, file me save nahi hogi</small>
</div>

<div class="box">
<h2>➕ Add Telegram Account (Send OTP)</h2>
<form method="post" action="/send_otp">
<input name="api_id" placeholder="API ID" required>
<input name="api_hash" placeholder="API HASH" required>
<input name="phone" placeholder="+91xxxxxxxxxx" required>
<button>Send OTP</button>
</form>
</div>

<div class="box">
<h2>📲 Verify OTP</h2>
<form method="post" action="/verify_otp">
<input name="phone" placeholder="+91xxxxxxxxxx" required>
<input name="otp" placeholder="OTP Code" required>
<button>Verify & Login</button>
</form>
</div>

<div class="box">
<h2>👤 Accounts</h2>
{% for p,a in accounts.items() %}
<b>{{p}}</b> — {{a["status"]}}
<form method="post" action="/start">
<input type="hidden" name="phone" value="{{p}}">
<button>Start Userbot</button>
</form>
<hr>
{% endfor %}
</div>

<div class="box">
<h2>🧠 GPT AI – Command Generator</h2>
<form method="post" action="/ai">
<textarea name="prompt" placeholder="Example: hi bole toh reply kare"></textarea>
<button>Generate Code</button>
</form>
{% if code %}
<h3>Generated Code</h3>
<pre>{{code}}</pre>
{% endif %}
</div>

</body>
</html>
"""

# ================= TELEGRAM FUNCTIONS =================
async def send_otp(api_id, api_hash, phone):
    client = TelegramClient(f"{SESS_DIR}/{phone}", api_id, api_hash)
    await client.connect()
    await client.send_code_request(phone)
    accounts[phone] = {
        "api_id": api_id,
        "api_hash": api_hash,
        "client": client,
        "status": "OTP_SENT"
    }

async def verify_otp(phone, otp):
    acc = accounts.get(phone)
    if not acc:
        return
    await acc["client"].sign_in(phone, otp)
    clients[phone] = acc["client"]
    acc["status"] = "LOGGED_IN"

async def start_userbot(phone):
    client = clients.get(phone)
    if not client:
        return

    @client.on(events.NewMessage(pattern="(?i)^hi$"))
    async def hi_handler(event):
        await event.reply("Hello 👋 (KAALIX Userbot)")

    await client.start()
    accounts[phone]["status"] = "RUNNING"
    await client.run_until_disconnected()

# ================= FLASK APP =================
app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string(HTML, accounts=accounts)

@app.route("/set_ai", methods=["POST"])
def set_ai():
    openai.api_key = request.form["key"].strip()
    return redirect("/")

@app.route("/send_otp", methods=["POST"])
def sendotp():
    api_id = int(request.form["api_id"])
    api_hash = request.form["api_hash"]
    phone = request.form["phone"]
    asyncio.run(send_otp(api_id, api_hash, phone))
    return redirect("/")

@app.route("/verify_otp", methods=["POST"])
def verifyotp():
    phone = request.form["phone"]
    otp = request.form["otp"]
    asyncio.run(verify_otp(phone, otp))
    return redirect("/")

@app.route("/start", methods=["POST"])
def start():
    phone = request.form["phone"]
    threading.Thread(
        target=lambda: asyncio.run(start_userbot(phone)),
        daemon=True
    ).start()
    return redirect("/")

@app.route("/ai", methods=["POST"])
def ai():
    prompt = request.form["prompt"]
    if not openai.api_key:
        code = "# ERROR: OpenAI API key set nahi hai"
    else:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate safe Telethon userbot commands only."},
                    {"role": "user", "content": prompt}
                ]
            )
            code = resp.choices[0].message.content
        except Exception as e:
            code = f"# AI ERROR: {e}"

    return render_template_string(HTML, accounts=accounts, code=code)

# ================= MAIN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
