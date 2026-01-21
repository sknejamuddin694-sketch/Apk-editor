#!/usr/bin/env python3
import asyncio, os, random, re, json
from aiohttp import web
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from telethon.errors import FloodWaitError, RPCError

# ---------------- CONFIG ---------------- #

HOST = "127.0.0.1"
PORT = 8080
SESSIONS = "sessions"
os.makedirs(SESSIONS, exist_ok=True)

clients = {}

# ---------------- UTIL ---------------- #

def parse_link(link):
    try:
        if "t.me/c/" in link:
            m = re.search(r"t\.me/c/(\d+)/(\d+)", link)
            return int("-100" + m.group(1)), int(m.group(2))
        else:
            m = re.search(r"t\.me/([^/]+)/(\d+)", link)
            return m.group(1), int(m.group(2))
    except:
        return None, None

async def load_sessions():
    for f in os.listdir(SESSIONS):
        if f.endswith(".session"):
            phone = f.replace(".session", "")
            client = TelegramClient(
                os.path.join(SESSIONS, phone),
                2040,
                "b18441a1ff76510619e3c197d826dd45"
            )
            await client.connect()
            if await client.is_user_authorized():
                clients[phone] = client
                print(f"✅ Session Restored: {phone}")

# ---------------- UI ---------------- #

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Nexus Reaction Panel</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;font-family:sans-serif;background:#0f172a;color:#fff}
nav{width:80px;position:fixed;height:100vh;background:#020617;display:flex;flex-direction:column;align-items:center;padding-top:20px}
nav div{margin:20px;cursor:pointer}
main{margin-left:80px;padding:30px}
.page{display:none}
.page.active{display:block}
input,select,button{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:none}
button{background:#2563eb;color:white;font-weight:bold}
.log{background:black;color:#22c55e;height:150px;overflow:auto;padding:10px;font-family:monospace}
</style>
</head>
<body>

<nav>
<div onclick="show('home',this)">🏠</div>
<div onclick="show('add',this)">➕</div>
<div onclick="show('react',this)">❤️</div>
</nav>

<main>
<div id="home" class="page active">
<h2>Dashboard</h2>
<p>Active Accounts: <span id="cnt">0</span></p>
</div>

<div id="add" class="page">
<h2>Add Account</h2>
<input id="api_id" placeholder="API ID">
<input id="api_hash" placeholder="API HASH">
<input id="phone" placeholder="+91xxxx">
<button onclick="sendOTP()">Send OTP</button>
<input id="otp" placeholder="OTP">
<input id="pwd" placeholder="2FA Password">
<button onclick="verify()">Login</button>
<div id="msg"></div>
</div>

<div id="react" class="page">
<h2>Mass Reaction</h2>
<input id="link" placeholder="https://t.me/...">
<select id="emoji">
<option value="❤️">❤️</option>
<option value="🔥">🔥</option>
<option value="👍">👍</option>
<option value="😂">😂</option>
</select>
<button onclick="react()">Start</button>
<div class="log" id="log"></div>
</div>
</main>

<script>
function show(id,el){
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
document.getElementById(id).classList.add('active');
}
async function status(){
let r=await fetch('/status');let d=await r.json();
document.getElementById('cnt').innerText=d.accounts;
}
setInterval(status,3000);status();

function log(t){let l=document.getElementById('log');l.innerHTML+="> "+t+"<br>";l.scrollTop=l.scrollHeight;}

async function sendOTP(){
let r=await fetch('/send_otp',{method:'POST',body:JSON.stringify({
api_id:api_id.value,api_hash:api_hash.value,phone:phone.value})});
let d=await r.json();msg.innerText=d.message||d.error;
}
async function verify(){
let r=await fetch('/verify',{method:'POST',body:JSON.stringify({
phone:phone.value,otp:otp.value,password:pwd.value})});
let d=await r.json();msg.innerText=d.message||d.error;status();
}
async function react(){
log("Starting...");
let r=await fetch('/react',{method:'POST',body:JSON.stringify({
link:link.value,emoji:emoji.value})});
let d=await r.json();log(d.message||d.error);
}
</script>
</body>
</html>
"""

# ---------------- ROUTES ---------------- #

async def index(request):
    return web.Response(text=HTML_TEMPLATE, content_type="text/html")

async def status(request):
    return web.json_response({"accounts": len(clients)})

async def send_otp(request):
    try:
        d = await request.json()
        phone = d["phone"].replace("+","")
        client = TelegramClient(
            os.path.join(SESSIONS, phone),
            int(d["api_id"]),
            d["api_hash"]
        )
        await client.connect()
        await client.send_code_request(d["phone"])
        clients[d["phone"]] = client
        return web.json_response({"message": "OTP Sent"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def verify(request):
    try:
        d = await request.json()
        client = clients[d["phone"]]
        try:
            await client.sign_in(d["phone"], d["otp"])
        except errors.SessionPasswordNeededError:
            await client.sign_in(password=d["password"])
        return web.json_response({"message": "Account Connected"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

# ---------------- FIXED REACTION ---------------- #

async def react_handler(request):
    d = await request.json()
    peer, msg_id = parse_link(d["link"])
    if not peer:
        return web.json_response({"error": "Invalid link"}, status=400)

    ok = 0
    for phone, client in list(clients.items()):
        try:
            if not await client.is_user_authorized():
                continue

            entity = await client.get_input_entity(peer)
            await client(
                SendReactionRequest(
                    peer=entity,
                    msg_id=msg_id,
                    reaction=[ReactionEmoji(emoticon=d["emoji"])]
                )
            )
            ok += 1
            await asyncio.sleep(random.uniform(1.2, 2.0))

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)
        except RPCError:
            continue
        except Exception:
            continue

    return web.json_response({"message": f"✅ Reacted with {ok} accounts"})

# ---------------- START ---------------- #

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/status", status)
app.router.add_post("/send_otp", send_otp)
app.router.add_post("/verify", verify)
app.router.add_post("/react", react_handler)

async def main():
    await load_sessions()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"🚀 Panel running at http://{HOST}:{PORT}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
