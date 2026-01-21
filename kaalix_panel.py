#!/usr/bin/env python3
import asyncio, os, random, re, json, subprocess
from aiohttp import web
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import ReactionEmoji
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
import yt_dlp

# ---------------- CONFIG ----------------
HOST = "127.0.0.1"
PORT = 8080
SESSIONS = "sessions"
os.makedirs(SESSIONS, exist_ok=True)

clients = {}
vc_clients = {}

# ---------------------------------------

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
            phone = f.replace(".session","")
            client = TelegramClient(os.path.join(SESSIONS, phone), 2040, "b18441a1ff76510619e3c197d826dd45")
            await client.connect()
            if await client.is_user_authorized():
                clients[phone] = client
                vc_clients[phone] = PyTgCalls(client)
                await vc_clients[phone].start()
                print(f"✅ Restored: {phone}")

# ---------------- YT AUDIO ----------------
def download_audio(url):
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "music.%(ext)s",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for f in os.listdir():
        if f.startswith("music."):
            return f
    return None

# ---------------- ROUTES ----------------

async def handle_index(request):
    return web.Response(text="Panel Running", content_type="text/html")

async def handle_status(request):
    return web.json_response({"accounts": len(clients)})

async def handle_send_otp(request):
    data = await request.json()
    phone = data['phone'].replace("+","")
    client = TelegramClient(os.path.join(SESSIONS, phone), int(data['api_id']), data['api_hash'])
    await client.connect()
    await client.send_code_request(data['phone'])
    clients[phone] = client
    vc_clients[phone] = PyTgCalls(client)
    await vc_clients[phone].start()
    return web.json_response({"message": "OTP Sent"})

async def handle_verify(request):
    data = await request.json()
    client = clients.get(data['phone'].replace("+",""))
    try:
        await client.sign_in(data['phone'], data['otp'])
    except errors.SessionPasswordNeededError:
        await client.sign_in(password=data['password'])
    return web.json_response({"message": "Login Success"})

# ---------- FIXED MASS REACTION ----------
async def handle_react(request):
    data = await request.json()
    peer, msg_id = parse_link(data['link'])
    if not peer:
        return web.json_response({"error": "Invalid link"}, status=400)

    success = 0

    for phone, client in clients.items():
        try:
            if not client.is_connected():
                await client.connect()

            entity = await client.get_entity(peer)

            try:
                await client(JoinChannelRequest(entity))
            except:
                pass

            await client(SendReactionRequest(
                peer=entity,
                msg_id=msg_id,
                reaction=[ReactionEmoji(emoticon=data['emoji'])]
            ))

            success += 1
            await asyncio.sleep(random.uniform(1,2))

        except errors.FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print("Reaction error:", e)

    return web.json_response({"message": f"Reaction done by {success} accounts"})

# ---------- VC JOIN + MUSIC ----------
async def handle_play(request):
    data = await request.json()
    chat = data['chat']
    url = data['url']

    audio = download_audio(url)
    if not audio:
        return web.json_response({"error": "Download failed"}, status=400)

    joined = 0
    for phone, vc in vc_clients.items():
        try:
            await vc.join_group_call(
                chat,
                AudioPiped(audio, HighQualityAudio())
            )
            joined += 1
            break
        except Exception as e:
            print("VC error:", e)

    return web.json_response({"message": f"Music playing in VC ({joined} client)"})

# ---------------- SERVER ----------------
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/status', handle_status)
app.router.add_post('/send_otp', handle_send_otp)
app.router.add_post('/verify', handle_verify)
app.router.add_post('/react', handle_react)
app.router.add_post('/play', handle_play)

async def start():
    await load_sessions()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"🚀 Panel running at http://{HOST}:{PORT}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(start())
