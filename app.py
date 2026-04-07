import edge_tts
import asyncio
import os
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

# Render cho phép ghi file vào thư mục /tmp
OUTPUT_FILE = "/tmp/voice.mp3"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create_audio", methods=["POST"])
def create_audio():
    text = request.form.get("text", "")
    voice_type = request.form.get("voice", "nu_ke")

    # Mặc định cấu hình giọng nói
    voice = "vi-VN-HoaiMyNeural"
    rate = "+0%"
    pitch = "+0Hz"

    # Logic chọn giọng đọc của bạn
    if voice_type == "nu_truyen":
        voice = "vi-VN-HoaiMyNeural"; rate = "-5%"; pitch = "+20Hz"
    elif voice_type == "nu_ke":
        voice = "vi-VN-HoaiMyNeural"; rate = "+0%"; pitch = "+0Hz"
    elif voice_type == "nu_bac":
        voice = "vi-VN-HoaiMyNeural"; rate = "-10%"; pitch = "+10Hz"
    elif voice_type == "nu_nam":
        voice = "vi-VN-HoaiMyNeural"; rate = "+5%"; pitch = "+5Hz"
    elif voice_type == "nam_tram":
        voice = "vi-VN-NamMinhNeural"; rate = "-5%"; pitch = "-20Hz"
    elif voice_type == "nam_ke":
        voice = "vi-VN-NamMinhNeural"; rate = "+0%"; pitch = "+0Hz"
    elif voice_type == "nam_bac":
        voice = "vi-VN-NamMinhNeural"; rate = "-10%"; pitch = "-10Hz"
    elif voice_type == "nam_nam":
        voice = "vi-VN-NamMinhNeural"; rate = "+5%"; pitch = "-5Hz"
    elif voice_type == "nu_halazy":
        voice = "vi-VN-HoaiMyNeural"; rate = "-7%"; pitch = "+18Hz"
    elif voice_type == "nu_story_youtube":
        voice = "vi-VN-HoaiMyNeural"; rate = "-12%"; pitch = "+8Hz"

    # Hàm xử lý bất đồng bộ
    async def generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        await communicate.save(OUTPUT_FILE)

    # CHỈNH SỬA TẠI ĐÂY: Cách chạy asyncio an toàn trên Server
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate())
        loop.close()
    except Exception as e:
        print(f"Lỗi tạo audio: {e}")
        return "Có lỗi xảy ra khi tạo audio!", 500

    return render_template("index.html", audio=True)

@app.route("/download")
def download():
    # Kiểm tra file có tồn tại trước khi gửi
    if os.path.exists(OUTPUT_FILE):
        return send_file(OUTPUT_FILE, as_attachment=True)
    return "File không tồn tại!", 404

if __name__ == "__main__":
    # Render yêu cầu host 0.0.0.0 và lấy port từ môi trường
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
