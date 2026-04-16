import os
import asyncio
import edge_tts
import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
AUDIO_FOLDER = 'static/audio'
os.makedirs(AUDIO_FOLDER, exist_ok=True)

VOICE_CONFIGS = {
    "nu_truyen": ("vi-VN-HoaiMyNeural", "-5%", "+15%"),
    "nu_ke": ("vi-VN-HoaiMyNeural", "0%", "0%"),
    "nu_halazy": ("vi-VN-HoaiMyNeural", "-7%", "+12%"),
    "nu_story_youtube": ("vi-VN-HoaiMyNeural", "-12%", "+8%"),
    "nam_tram": ("vi-VN-NamMinhNeural", "-5%", "-15%"),
    "nam_ke": ("vi-VN-NamMinhNeural", "0%", "0%")
}


def split_text(text, limit=1800):
    chunks = []
    while len(text) > limit:
        idx = text.rfind('.', 0, limit)
        if idx == -1: idx = text.rfind(' ', 0, limit)
        if idx == -1: idx = limit
        chunks.append(text[:idx + 1].strip())
        text = text[idx + 1:].strip()
    if text: chunks.append(text)
    return chunks


async def download_chunk(chunk, voice_args, path):
    """Hàm tải một đoạn audio riêng lẻ"""
    communicate = edge_tts.Communicate(chunk, **voice_args)
    await communicate.save(path)
    return path


@app.route('/')
def index():
    labels = {k: v for k, v in zip(VOICE_CONFIGS.keys(),
                                   ["Nữ - Đọc truyện", "Nữ - Kể chuẩn", "Nữ - Halazy", "Nữ - YouTube", "Nam - Trầm",
                                    "Nam - Kể"])}
    return render_template('index.html', voices=labels)


@app.route('/generate', methods=['POST'])
def generate():
    try:
        text = request.form.get('text', '').strip()
        voice_key = request.form.get('voice')
        user_speed = request.form.get('speed', '1.0')

        if not text: return jsonify({"error": "Văn bản trống"}), 400

        short_name, base_rate, pitch = VOICE_CONFIGS[voice_key]
        u_speed = float(user_speed)
        total_rate = int((u_speed - 1.0) * 100) + int(base_rate.replace('%', ''))

        tts_args = {"voice": short_name}
        if total_rate != 0: tts_args['rate'] = f"{total_rate:+d}%"
        if pitch not in ["0%", "0Hz"]: tts_args['pitch'] = pitch

        text_chunks = split_text(text)
        session_id = int(time.time())
        final_filename = f"audio_{session_id}.mp3"
        final_path = os.path.join(AUDIO_FOLDER, final_filename)

        async def run_parallel():
            tasks = []
            temp_paths = []

            # 1. Tạo danh sách các công việc tải cùng lúc
            for i, chunk in enumerate(text_chunks):
                t_path = os.path.join(AUDIO_FOLDER, f"temp_{session_id}_{i}.mp3")
                temp_paths.append(t_path)
                tasks.append(download_chunk(chunk, tts_args, t_path))

            # 2. Kích hoạt tải song song tất cả các đoạn
            await asyncio.gather(*tasks)

            # 3. Nối file (chỉ tốn vài mili giây)
            with open(final_path, 'wb') as final_file:
                for t_path in temp_paths:
                    if os.path.exists(t_path):
                        with open(t_path, 'rb') as f:
                            final_file.write(f.read())
                        try:
                            os.remove(t_path)
                        except:
                            pass

        # Chạy toàn bộ tiến trình
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_parallel())

        return jsonify({"audio_url": f"/static/audio/{final_filename}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7777)
