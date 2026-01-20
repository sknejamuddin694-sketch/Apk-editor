#!/usr/bin/env python3
import os, asyncio
from flask import Flask, request, render_template_string
from telethon import TelegramClient, events, errors
import openai

# ================= BASIC CONFIG =================
PORT = int(os.environ.get("PORT", 8080))
SESS_DIR = "sessions"
os.makedirs(SESS_DIR, exist_ok=True)

# ---------- GLOBAL STATE (single user demo) ----------
STATE = {
    "step": "idle",  # idle, api, phone, otp, password, ai, done
    "api_id": None,
    "api_hash": None,
    "phone": None,
    "client": None,
    "logged": False,
    "need_password": False,
    "ai_key": "",
}

app = Flask(__name__)

# ================= HTML =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>KAALIX LOGIN PANEL</title>
<style>
body{background:#0b0e14;color:#eee;font-family:Arial}
.box{background:#111;padding:20px;margin:20px;border-radius:10px}
input,textarea,button{width:100%;padding:10px;margin:6px 0}
button{background:#4caf50;border:none;font-weight:bold}
pre{background:#000;padding:10px;white-space:pre-wrap}
small{color:#aaa}
</style>
</head>
<body>

<div class="box">
<h2>➕ Add Telegram Account</h2>

<form method="post">
{% if step == "idle" %}
<button name="action" value="start">Start Login</button>

{% elif step == "api" %}
<input name="api_id" placeholder="API ID" required>
<input name="api_hash" placeholder="API HASH" required>
<button>Next</button>

{% elif step == "phone" %}
<input name="phone" placeholder="+91xxxxxxxxxx" required>
<button>Send OTP</button>
<small>OTP Telegram app me aayega</small>

{% elif step == "otp" %}
<input name="otp" placeholder="Enter OTP" required>
<button>Verify OTP</button>

{% elif step == "password" %}
<input name="password" placeholder="2FA Password">
<button>Verify Password</button>

{% elif step == "ai" %}
<input name="ai_key" placeholder="OpenAI API Key (sk-...)" required>
<button>Finish Login</button>
{% endif %}
</form>

<p>Current step: {{step}}</p>
</div>

{% if logged %}
<div class="box">
<h2>🧠 AI BOX (Account Connected)</h2>
<form method="post" action="/ai">
<textarea name="prompt" placeholder="AI command likho..."></textarea>
<button>Run AI</button>
</form>

{% if result %}
<pre>{{result}}</pre>
{% endif %}
</div>
{% endif %}

</body>
</html>
"""

# ================= ROUTES =================
@app.route("/", methods=["GET","POST"])
def index():
    global STATE
    result = None

    if request.method == "POST":
        try:
            # ---------- START ----------
            if STATE["step"] == "idle":
                STATE["step"] = "api"

            # ---------- API ----------
            elif STATE["step"] == "api":
                STATE["api_id"] = int(request.form["api_id"])
                STATE["api_hash"] = request.form["api_hash"]
                STATE["step"] = "phone"

            # ---------- PHONE ----------
            elif STATE["step"] == "phone":
                STATE["phone"] = request.form["phone"]
                client = TelegramClient(
                    f"{SESS_DIR}/{STATE['phone']}",
                    STATE["api_id"],
                    STATE["api_hash"]
                )
                asyncio.run(client.connect())
                asyncio.run(client.send_code_request(STATE["phone"]))
                STATE["client"] = client
                STATE["step"] = "otp"

            # ---------- OTP ----------
            elif STATE["step"] == "otp":
                try:
                    asyncio.run(
                        STATE["client"].sign_in(
                            STATE["phone"],
                            request.form["otp"]
                        )
                    )
                    STATE["step"] = "ai"
                except errors.SessionPasswordNeededError:
                    STATE["step"] = "password"

            # ---------- PASSWORD ----------
            elif STATE["step"] == "password":
                asyncio.run(
                    STATE["client"].sign_in(
                        password=request.form["password"]
                    )
                )
                STATE["step"] = "ai"

            # ---------- AI KEY ----------
            elif STATE["step"] == "ai":
                STATE["ai_key"] = request.form["ai_key"]
                openai.api_key = STATE["ai_key"]
                STATE["logged"] = True
                STATE["step"] = "done"

        except Exception as e:
            result = f"ERROR: {e}"

    return render_template_string(
        HTML,
        step=STATE["step"],
        logged=STATE["logged"],
        result=result
    )

@app.route("/ai", methods=["POST"])
def ai():
    prompt = request.form["prompt"]
    try:
        r = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        out = r.choices[0].message.content
    except Exception as e:
        out = f"AI ERROR: {e}"

    return render_template_string(
        HTML,
        step="done",
        logged=True,
        result=out
    )

# ================= MAIN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
