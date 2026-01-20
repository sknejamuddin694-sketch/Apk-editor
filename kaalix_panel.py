import os
import threading
import whisper
import openai
from flask import Flask, request, send_file, render_template_string
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

WORKDIR = "work"
os.makedirs(WORKDIR, exist_ok=True)

whisper_model = whisper.load_model("base")

BOT_APP = None
BOT_RUNNING = False

# ================= VOICE DECISION =================
def decide_voice(jp_text):
    male_words = ["俺", "僕", "だぞ", "だろ", "くそ"]
    female_words = ["私", "あたし", "よね", "わ", "かしら"]
    for w in male_words:
        if w in jp_text:
            return "male"
    for w in female_words:
        if w in jp_text:
            return "female"
    return "female"

# ================= CORE DUB =================
def process_video(input_video, output_video):
    video = VideoFileClip(input_video)
    jp_audio = f"{WORKDIR}/jp.wav"
    video.audio.write_audiofile(jp_audio, logger=None)

    result = whisper_model.transcribe(jp_audio, language="ja")
    segments = result["segments"]

    clips = []
    for i, seg in enumerate(segments):
        jp_line = seg["text"].strip()
        if not jp_line:
            continue

        tr = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Translate Japanese anime dialogue into simple spoken Hindi"},
                {"role": "user", "content": jp_line}
            ]
        )
        hi_text = tr.choices[0].message.content
        voice = decide_voice(jp_line)

        speech = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=hi_text
        )

        part = f"{WORKDIR}/p{i}.wav"
        with open(part, "wb") as f:
            f.write(speech)
        clips.append(AudioFileClip(part))

    final_audio = concatenate_audioclips(clips)
    final_video = video.set_audio(final_audio)
    final_video.write_videofile(output_video, logger=None)

# ================= TELEGRAM BOT =================
async def tg_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Hindi dub shuru… wait karo ⏳")
    file = await update.message.video.get_file()
    inp = f"{WORKDIR}/tg_input.mp4"
    out = f"{WORKDIR}/tg_output.mp4"
    await file.download_to_drive(inp)
    process_video(inp, out)
    await update.message.reply_video(video=open(out, "rb"))

def start_bot(token):
    global BOT_APP, BOT_RUNNING
    if BOT_RUNNING:
        return
    BOT_RUNNING = True
    BOT_APP = ApplicationBuilder().token(token).build()
    BOT_APP.add_handler(MessageHandler(filters.VIDEO, tg_video))
    BOT_APP.run_polling()

# ================= HTML =================
app = Flask(__name__)

HTML = """
<h2>Anime Hindi Dub Control Panel</h2>
<form method="post">
OpenAI API Key:<br>
<input name="openai" required><br><br>
Telegram Bot Token:<br>
<input name="bot" required><br><br>
<button>START BOT</button>
</form>
<hr>
<h3>Web Upload (Bot must be running)</h3>
<form method=post enctype=multipart/form-data action="/upload">
<input type=file name=video required>
<button>Dub Video</button>
</form>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        openai.api_key = request.form["openai"]
        bot_token = request.form["bot"]
        threading.Thread(target=start_bot, args=(bot_token,)).start()
        return "<h3>✅ Bot Started. Now send video on Telegram OR upload below.</h3>"
    return render_template_string(HTML)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["video"]
    inp = f"{WORKDIR}/web_input.mp4"
    out = f"{WORKDIR}/web_output.mp4"
    f.save(inp)
    process_video(inp, out)
    return send_file(out, as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
