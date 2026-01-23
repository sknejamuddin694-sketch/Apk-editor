#!/usr/bin/env python3
import os
import re
import asyncio
import subprocess
from aiohttp import web
from telethon import TelegramClient, events, errors

# ---------------- GLOBALS ----------------
BASE_DIR = os.getcwd()
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

client = None
phone_code_hash = None
phone_number = None
api_id = None
api_hash = None
session_name = None
BOT_USERNAME = "Engine_KeyGen_bot"

# ---------------- HTML PANEL ----------------
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PREMIUM TELEGRAM CONTROL v2.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --primary: #00f5ff;
            --secondary: #7c3aed;
            --accent: #00ff88;
            --danger: #ff4768;
            --bg: #0a0a0f;
            --card-bg: rgba(15, 15, 25, 0.6);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --border: rgba(255, 255, 255, 0.08);
            --glow: rgba(0, 245, 255, 0.3);
            --success-glow: rgba(0, 255, 136, 0.3);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--bg);
            color: #f0f0f5;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* Premium Particle Background */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }

        .particle {
            position: absolute;
            background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
            border-radius: 50%;
            animation: float 20s infinite linear;
        }

        @keyframes float {
            0% { transform: translateY(100vh) scale(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100px) scale(1); opacity: 0; }
        }

        /* Main Container */
        .container {
            max-width: 480px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 10;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            animation: slideUpFade 1s ease-out;
        }

        .logo {
            font-size: clamp(2rem, 8vw, 4rem);
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 50%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -2px;
            position: relative;
        }

        .logo::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
            border-radius: 2px;
            animation: glowPulse 2s ease-in-out infinite;
        }

        /* Section Styling */
        .section {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 
                0 25px 45px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            animation: slideUpFade 0.8s ease-out forwards;
            opacity: 0;
            transform: translateY(30px);
        }

        .section:nth-child(2) { animation-delay: 0.1s; }
        .section:nth-child(3) { animation-delay: 0.2s; }
        .section:nth-child(4) { animation-delay: 0.3s; }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--primary);
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title i {
            font-size: 16px;
            animation: ping 2s infinite;
        }

        /* Input Groups */
        .input-group {
            margin-bottom: 18px;
            position: relative;
        }

        .input-group input {
            width: 100%;
            padding: 16px 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1.5px solid var(--border);
            border-radius: 16px;
            color: #fff;
            font-size: 16px;
            font-weight: 400;
            backdrop-filter: blur(10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .input-group input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .input-group input:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 
                0 0 0 4px rgba(0, 245, 255, 0.15),
                0 8px 32px rgba(0, 245, 255, 0.1);
            transform: translateY(-1px);
        }

        /* Premium Buttons */
        .btn {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            box-shadow: 0 8px 32px rgba(0, 245, 255, 0.3);
            color: #000;
        }

        .btn-primary:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 16px 48px rgba(0, 245, 255, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--accent) 0%, #00d084 100%);
            box-shadow: 0 8px 32px rgba(0, 255, 136, 0.3);
            color: #000;
        }

        .btn-success:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 16px 48px rgba(0, 255, 136, 0.4);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.03);
            border: 1.5px solid var(--border);
            color: #fff;
            backdrop-filter: blur(10px);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(0, 245, 255, 0.2);
        }

        /* File Upload */
        .file-input-wrapper {
            position: relative;
            background: rgba(255, 255, 255, 0.03);
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 16px;
        }

        .file-input-wrapper:hover {
            border-color: var(--primary);
            background: rgba(0, 245, 255, 0.05);
        }

        .file-input-wrapper input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }

        /* Status & Output */
        #status {
            text-align: center;
            font-size: 15px;
            font-weight: 500;
            margin: 20px 0;
            min-height: 20px;
            padding: 12px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }

        #output {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid var(--accent);
            border-radius: 12px;
            padding: 16px;
            font-family: 'Courier New', monospace;
            color: var(--accent);
            font-size: 13px;
            white-space: pre-wrap;
            overflow-x: auto;
            margin-top: 16px;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
            display: none;
            animation: slideUpFade 0.5s ease-out;
        }

        /* Animations */
        @keyframes slideUpFade {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes glowPulse {
            0%, 100% { opacity: 0.6; transform: translateX(-50%) scale(1); }
            50% { opacity: 1; transform: translateX(-50%) scale(1.1); }
        }

        @keyframes shimmer {
            0% { background-position: -468px 0; }
            100% { background-position: 468px 0; }
        }

        /* Responsive */
        @media (max-width: 480px) {
            .container { padding: 16px; }
            .section { padding: 20px; }
        }

        /* Loading Overlay */
        .loading {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }

        .loading.active {
            opacity: 1;
            visibility: visible;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(0, 245, 255, 0.2);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Premium Particle System -->
    <div class="particles" id="particles"></div>

    <!-- Loading Overlay -->
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>

    <div class="container">
        <div class="header">
            <h1 class="logo">
                <i class="fas fa-crown"></i> PREMIUM PANEL
            </h1>
            <div style="font-size: 14px; color: #888; margin-top: 8px;">v2.0 Elite Edition</div>
        </div>

        <!-- Authentication Section -->
        <div class="section">
            <div class="section-title">
                <i class="fas fa-shield-alt"></i> Authentication
            </div>
            <div class="input-group"><input id="api_id" placeholder="API ID" required></div>
            <div class="input-group"><input id="api_hash" placeholder="API HASH" required></div>
            <div class="input-group"><input id="phone" placeholder="+91 00000 00000" required></div>
            <button class="btn btn-primary" onclick="sendOtp()">
                <i class="fas fa-paper-plane"></i> Send OTP
            </button>
            
            <div style="margin-top: 24px;">
                <div class="input-group"><input id="otp" placeholder="Enter OTP Code"></div>
                <div class="input-group"><input id="password" type="password" placeholder="2FA Password (if enabled)"></div>
                <button class="btn btn-primary" onclick="login()">
                    <i class="fas fa-lock-open"></i> Authorize Access
                </button>
            </div>
        </div>

        <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); margin: 32px 0;">

        <!-- Executor Section -->
        <div class="section">
            <div class="section-title">
                <i class="fas fa-play-circle"></i> Executor
            </div>
            <form id="uploadForm">
                <div class="file-input-wrapper">
                    <i class="fas fa-cloud-upload-alt" style="font-size: 24px; color: var(--primary); margin-bottom: 8px;"></i>
                    <div style="color: #888;">Click to upload script</div>
                    <input type="file" name="file" accept=".py,.js,.php">
                </div>
                <button type="submit" class="btn btn-secondary">
                    <i class="fas fa-upload"></i> Upload Script
                </button>
            </form>
            <button class="btn btn-success" onclick="runFile()">
                <i class="fas fa-rocket"></i> ▶ Run Instance
            </button>
        </div>

        <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); margin: 32px 0;">

        <!-- License Section -->
        <div class="section">
            <div class="section-title">
                <i class="fas fa-key"></i> License Management
            </div>
            <button class="btn btn-secondary" onclick="generateKey()">
                <i class="fas fa-magic"></i> 🔑 Generate Elite Key
            </button>
        </div>

        <div id="status"></div>
        <pre id="output"></pre>
    </div>

    <script>
        // Premium Particle System
        function createParticles() {
            const particles = document.getElementById('particles');
            for (let i = 0; i < 15; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.width = particle.style.height = (Math.random() * 6 + 2) + 'px';
                particle.style.animationDuration = (Math.random() * 15 + 15) + 's';
                particle.style.animationDelay = Math.random() * 5 + 's';
                particles.appendChild(particle);
            }
        }

        // UI Enhancements
        function showLoading(show) {
            const loading = document.getElementById('loading');
            if (show) {
                loading.classList.add('active');
            } else {
                loading.classList.remove('active');
            }
        }

        function statusMsg(text, type = 'info') {
            const status = document.getElementById('status');
            status.innerText = text;
            const colors = {
                success: '#00ff88',
                error: '#ff4768',
                info: '#00f5ff',
                warning: '#ffb800'
            };
            status.style.color = colors[type] || colors.info;
            status.style.background = `rgba(${type === 'success' ? '0,255,136' : type === 'error' ? '255,71,104' : '0,245,255'}, 0.1)`;
            status.style.border = `1px solid ${colors[type] || colors.info}`;
        }

        // Original Functions Enhanced
        async function post(url, data) {
            showLoading(true);
            try {
                const response = await fetch(url, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showLoading(false);
                return result;
            } catch (error) {
                showLoading(false);
                statusMsg('Network Error: ' + error.message, 'error');
                throw error;
            }
        }

        async function sendOtp() {
            const api_id = document.getElementById('api_id');
            const api_hash = document.getElementById('api_hash');
            const phone = document.getElementById('phone');
            
            if (!api_id.value || !api_hash.value || !phone.value) {
                statusMsg('⚠️ Please fill all fields', 'warning');
                return;
            }
            
            statusMsg('⏳ Sending OTP...', 'info');
            let r = await post('/send_otp', {
                api_id: api_id.value,
                api_hash: api_hash.value,
                phone: phone.value
            });
            statusMsg(r.message || 'OTP Sent Successfully!', 'success');
        }

        async function login() {
            const otp = document.getElementById('otp');
            const password = document.getElementById('password');
            
            if (!otp.value) {
                statusMsg('⚠️ Enter OTP Code', 'warning');
                return;
            }
            
            statusMsg('🔐 Authenticating...', 'info');
            let r = await post('/login', {
                otp: otp.value,
                password: password.value || ''
            });
            statusMsg(r.message || 'Login Successful! 🚀', 'success');
        }

        document.getElementById('uploadForm').onsubmit = async (e) => {
            e.preventDefault();
            statusMsg('📤 Uploading script...', 'info');
            let fd = new FormData(e.target);
            showLoading(true);
            try {
                let r = await fetch('/upload', { method: 'POST', body: fd });
                let j = await r.json();
                statusMsg(j.message || 'Upload Successful!', 'success');
            } catch (error) {
                statusMsg('Upload Failed: ' + error.message, 'error');
            }
            showLoading(false);
        };

        async function runFile() {
            statusMsg('🚀 Executing instance...', 'info');
            let r = await post('/run', {});
            statusMsg(r.message || 'Instance Running!', 'success');
        }

        async function generateKey() {
            statusMsg('🔑 Generating Elite License...', 'info');
            let r = await post('/generate_key', {});
            const output = document.getElementById('output');
            if (r.status === 'success') {
                output.innerText = r.license_key;
                output.style.display = 'block';
                statusMsg('✅ Elite Key Generated Successfully!', 'success');
            } else {
                statusMsg('❌ ' + (r.reason || 'Generation Failed'), 'error');
            }
        }

        // Enter Key Support
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const active = document.activeElement;
                if (active.id === 'otp') login();
                if (active.id === 'api_id' || active.id === 'api_hash' || active.id === 'phone') sendOtp();
            }
        });

        // Initialize Premium Effects
        window.addEventListener('load', () => {
            createParticles();
            document.querySelectorAll('.section').forEach((sec, i) => {
                sec.style.animationDelay = `${i * 0.1}s`;
            });
        });
    </script>
</body>
</html>
"""

# ---------------- HELPER ----------------
async def click_button(msg, text_pattern):
    if not msg.buttons:
        return False
    for row in msg.buttons:
        for btn in row:
            if text_pattern.lower() in btn.text.lower():
                await btn.click()
                return True
    return False

async def generate_key_logic():
    global client
    if not client or not await client.is_user_authorized():
        return "Error: Not logged in"
    try:
        async with client.conversation(BOT_USERNAME, timeout=40) as conv:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.send_message("🔑 Generate Key")
            msg = await conv.get_response()
            await asyncio.sleep(1)
            await click_button(msg,"12 Hrs")
            await conv.send_message("1")
            await conv.send_message("Elite")

            # Wait for key
            for _ in range(25):
                msgs = await client.get_messages(BOT_USERNAME, limit=5)
                for m in msgs:
                    if m.text:
                        match = re.search(r"(Elite-[A-Za-z0-9-]+)", m.text)
                        if match:
                            return match.group(1)
                await asyncio.sleep(1)
        return "Key not found"
    except Exception as e:
        return str(e)

# ---------------- TELEGRAM COMMAND ----------------
async def register_handler():
    @client.on(events.NewMessage(pattern="/key"))
    async def handler(e):
        m = await e.reply("⏳ Generating key...")
        k = await generate_key_logic()
        if k:
            await m.edit(f"✅ Key:\n`{k}`")
        else:
            await m.edit("❌ Failed to generate key")

# ---------------- ROUTES ----------------
async def index(req):
    return web.Response(text=HTML, content_type="text/html")

async def send_otp(req):
    global client, phone_number, phone_code_hash, api_id, api_hash, session_name
    d = await req.json()
    api_id = int(d["api_id"]) if d["api_id"] else None
    api_hash = d["api_hash"] if d["api_hash"] else None
    phone_number = d["phone"]
    session_name = f"{SESSIONS_DIR}/{phone_number.replace('+','')}"
    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()
    if await client.is_user_authorized():
        await register_handler()
        return web.json_response({"message":"✅ Already logged in"})
    sent = await client.send_code_request(phone_number)
    phone_code_hash = sent.phone_code_hash
    return web.json_response({"message":"📩 OTP sent"})

async def login(req):
    global client
    d = await req.json()
    try:
        await client.sign_in(phone_number, d["otp"], phone_code_hash=phone_code_hash)
        await register_handler()
        return web.json_response({"message":"✅ Login successful"})
    except errors.SessionPasswordNeededError:
        await client.sign_in(password=d.get("password"))
        await register_handler()
        return web.json_response({"message":"✅ Login with 2FA"})
    except Exception as e:
        return web.json_response({"message":str(e)})

async def upload_file(req):
    reader = await req.multipart()
    part = await reader.next()
    filename = part.filename
    path = os.path.join(UPLOADS_DIR, filename)
    with open(path, "wb") as f:
        f.write(await part.read())
    return web.json_response({"message":"✅ File uploaded"})

async def run_file(req):
    files = os.listdir(UPLOADS_DIR)
    if not files:
        return web.json_response({"message":"❌ No uploaded file"})
    file_path = os.path.join(UPLOADS_DIR, files[0])
    subprocess.Popen(["python", file_path])
    return web.json_response({"message":"🚀 Running uploaded file"})

async def generate_key_api(req):
    k = await generate_key_logic()
    if "Elite-" in k:
        return web.json_response({"status":"success","license_key":k})
    return web.json_response({"status":"failed","reason":k}, status=500)

# ---------------- MAIN ----------------
async def main():
    await client.start() if client else None
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/send_otp", send_otp)
    app.router.add_post("/login", login)
    app.router.add_post("/upload", upload_file)
    app.router.add_post("/run", run_file)
    app.router.add_post("/generate_key", generate_key_api)

    runner = web.AppRunner(app)
    await runner.setup()
    PORT = int(os.environ.get("PORT",8780))
    site = web.TCPSite(runner,"0.0.0.0",PORT)
    await site.start()
    print(f"🌐 Panel running → http://127.0.0.1:{PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
