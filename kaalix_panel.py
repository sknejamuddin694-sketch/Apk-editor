# ================== CONFIG (PASTE HERE) ==================
BOT_TOKEN = "8507388502:AAFN-A33sRl6uqfy--EShYHXtuhisY06Z9k"
OPENAI_API_KEY = "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"
# =========================================================

import os
import threading
import whisper
import openai
from flask import Flask, request, send_file, render_template_string
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

openai.api_key = OPENAI_API_KEY

WORKDIR = "work"
os.makedirs(WORKDIR, exist_ok=True)

# ================= LOAD WHISPER =================
whisper_model = whisper.load_model("base")

# ================= VOICE DECISION =================
def decide_voice(jp_text):
    male_words = ["俺", "僕", "だぞ", "くそ", "だろ"]
    female_words = ["私", "あたし", "よね", "わ", "かしら"]

    for w in male_words:
        if w in jp_text:
            return "male"
    for w in female_words:
        if w in jp_text:
            return "female"
    return "female"  # default

# ================= CORE PROCESS =================
def process_video(input_video, output_video):
    video = VideoFileClip(input_video)
    jp_audio = f"{WORKDIR}/jp.wav"
    video.audio.write_audiofile(jp_audio, logger=None)

    # JP speech -> text with segments
    result = whisper_model.transcribe(jp_audio, language="ja")
    segments = result["segments"]

    hindi_audio_parts = []

    for i, seg in enumerate(segments):
        jp_line = seg["text"].strip()
        if not jp_line:
            continue

        # Translate to Hindi
        tr = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Translate Japanese anime dialogue into simple spoken Hindi"},
                {"role": "user", "content": jp_line}
            ]
        )
        hi_text = tr.choices[0].message.content

        voice = decide_voice(jp_line)

        # Hindi TTS
        speech = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=hi_text
        )

        part_path = f"{WORKDIR}/part_{i}.wav"
        with open(part_path, "wb") as f:
            f.write(speech)

        hindi_audio_parts.append(AudioFileClip(part_path))

    if not hindi_audio_parts:
        raise Exception("No dialogue detected")

    final_audio = concatenate_audioclips(hindi_audio_parts)
    final_video = video.set_audio(final_audio)
    final_video.write_videofile(output_video, logger=None)

# ================= TELEGRAM BOT =================
async def tg_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Video mil gaya\n"
        "🇯🇵➡️🇮🇳 Japanese → Hindi dub shuru\n"
        "👨/👩 Auto male-female voice\n"
        "⏳ Thoda wait..."
    )

    file = await update.message.video.get_file()
    inp = f"{WORKDIR}/tg_input.mp4"
    out = f"{WORKDIR}/tg_output.mp4"
    await file.download_to_drive(inp)

    t = threading.Thread(target=process_video, args=(inp, out))
    t.start()
    t.join()

    await update.message.reply_video(
        video=open(out, "rb"),
        caption="✅ Hindi Dub Ready (Auto Male/Female)"
    )

def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO, tg_video))
    print("🤖 Telegram Bot Running")
    app.run_polling()

# ================= HTML WEB =================
web = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<title>Anime Hindi Dub</title>
<h2>Upload Anime Clip (Max ~3 min)</h2>
<p>Auto Male / Female Hindi Voice</p>
<form method=post enctype=multipart/form-data>
  <input type=file name=video required>
  <br><br>
  <input type=submit value="Dub to Hindi">
</form>
"""

@web.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["video"]
        inp = f"{WORKDIR}/web_input.mp4"
        out = f"{WORKDIR}/web_output.mp4"
        file.save(inp)
        process_video(inp, out)
        return send_file(out, as_attachment=True)
    return render_template_string(HTML_PAGE)

# ================= MAIN =================
if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    web.run(host="0.0.0.0", port=8080)
