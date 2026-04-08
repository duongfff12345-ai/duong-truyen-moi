import edge_tts
import asyncio
import uuid
import os
from flask import Flask, render_template, request, send_file

app = Flask(__name__)


def generate_audio(text, voice, rate, pitch, filename):

    async def run_tts():
        ssml = f"""
        <speak version='1.0' xml:lang='vi-VN'>
            <voice name='{voice}'>
                <prosody rate='{rate}' pitch='{pitch}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """

        communicate = edge_tts.Communicate(ssml, voice)
        await communicate.save(filename)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_tts())
    loop.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create_audio", methods=["POST"])
def create_audio():

    text = request.form.get("text", "").strip()
    voice_type = request.form.get("voice", "")

    if text == "":
        return "Bạn chưa nhập nội dung!"

    voice = "vi-VN-HoaiMyNeural"
    rate = "+0%"
    pitch = "+0Hz"

    if voice_type == "nam":
        voice = "vi-VN-NamMinhNeural"

    filename = f"voice_{uuid.uuid4().hex}.mp3"

    try:
        generate_audio(text, voice, rate, pitch, filename)
    except Exception as e:
        return f"Lỗi tạo audio: {str(e)}"

    if not os.path.exists(filename):
        return "Không tạo được file mp3!"

    return render_template("index.html", audio=filename)


@app.route("/download/<filename>")
def download(filename):
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555)
