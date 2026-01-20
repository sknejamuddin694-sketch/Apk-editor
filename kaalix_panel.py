#!/usr/bin/env python3
import os, asyncio
from flask import Flask, request, render_template_string
from telethon import TelegramClient, errors, events
import openai

PORT = int(os.environ.get("PORT", 8080))
SESS_DIR = "sessions"
os.makedirs(SESS_DIR, exist_ok=True)

app = Flask(__name__)

STATE = {
    "step": 0,
    "api_id": "",
    "api_hash": "",
    "phone": "",
    "client": None,
    "logged": False,
    "ai_key": ""
}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>KAALIX PANEL</title>
<style>
body{background:#0b0e14;color:#eee;font-family:Arial}
.box{background:#111;padding:20px;margin:20px;border-radius:10px}
input,textarea,button{width:100%;padding:10px;margin:5px 0}
button{background:#4caf50;border:none;font-weight:bold}
pre{background:#000;padding:10px}
</style>
</head>
<body>

<div class="box">
<h2>➕ Add Account</h2>
<form method="post">
{% if step == 0 %}
<input name="api_id" placeholder="API ID" required>
<button>Next</button>

{% elif step == 1 %}
<input name="api_hash" placeholder="API HASH" required>
<button>Next</button>

{% elif step == 2 %}
<input name="phone" placeholder="+91xxxxxxxxxx" required>
<button>Send OTP</button>

{% elif step == 3 %}
<input name="otp" placeholder="OTP Code" required>
<button>Verify OTP</button>

{% elif step == 4 %}
<input name="password" placeholder="2FA Password (if any)">
<button>Verify Password</button>

{% elif step == 5 %}
<input name="ai_key" placeholder="OpenAI API Key (sk-...)" required>
<button>Finish Login</button>
{% endif %}
</form>

<p>Current Step: {{step}}</p>
</div>

{% if logged %}
<div class="box">
<h2>🧠 AI BOX (Account Connected)</h2>
<form method="post" action="/ai">
<textarea name="prompt" placeholder="command likho..."></textarea>
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

@app.route("/", methods=["GET","POST"])
def index():
    global STATE
    result = None

    if request.method == "POST":
        try:
            if STATE["step"] == 0:
                STATE["api_id"] = int(request.form["api_id"])
                STATE["step"] = 1

            elif STATE["step"] == 1:
                STATE["api_hash"] = request.form["api_hash"]
                STATE["step"] = 2

            elif STATE["step"] == 2:
                STATE["phone"] = request.form["phone"]
                client = TelegramClient(
                    f"{SESS_DIR}/{STATE['phone']}",
                    STATE["api_id"],
                    STATE["api_hash"]
                )
                asyncio.run(client.connect())
                asyncio.run(client.send_code_request(STATE["phone"]))
                STATE["client"] = client
                STATE["step"] = 3

            elif STATE["step"] == 3:
                try:
                    asyncio.run(
                        STATE["client"].sign_in(
                            STATE["phone"],
                            request.form["otp"]
                        )
                    )
                    STATE["step"] = 5
                except errors.SessionPasswordNeededError:
                    STATE["step"] = 4

            elif STATE["step"] == 4:
                asyncio.run(
                    STATE["client"].sign_in(
                        password=request.form["password"]
                    )
                )
                STATE["step"] = 5

            elif STATE["step"] == 5:
                STATE["ai_key"] = request.form["ai_key"]
                openai.api_key = STATE["ai_key"]
                STATE["logged"] = True

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
        step=STATE["step"],
        logged=True,
        result=out
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
