import os
import json
import tempfile
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from app import app

# 環境変数読み込み
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Flask と OpenAI クライアント初期化
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# インタビュアースクリプト読み込み
json_path = os.path.join(BASE_DIR, "interview_scripts.json")
with open(json_path, "r", encoding="utf-8") as f:
    SCRIPTS = json.load(f)

# app = Flask(__name__)   
# print("End reading scripts.json")

@app.route("/")
def index():
    print("index")
    return render_template("index.html", scripts=SCRIPTS)

@app.route("/ao")
def ao():
    print("ao index")
    return render_template("index.html", scripts=SCRIPTS)

@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.json
    text = data["motivation"]
    #print(f"Motivation: {text}")
    interviewer = data["interviewer"]
    history = [
        {"role": "system", "content": SCRIPTS[interviewer]["system_prompt"]},
        {"role": "user", "content": f"まずはこの志望理由を読んで、最初の質問を一つ生成してください:\n\n{text}"}
    ]
    res = client.chat.completions.create(
        model="gpt-4",
        messages=history
    )
    question = res.choices[0].message.content.strip()
    return jsonify({"question": question, "history": history})

@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.json
    text = data["text"]
    interviewer = data["interviewer"]
    tts = client.audio.speech.create(
        model="tts-1",
        voice=SCRIPTS[interviewer]["voice"],
        input=text
    )
    return (tts.content, 200, {"Content-Type": "audio/mpeg"})

@app.route("/api/interview", methods=["POST"])
def api_interview():
    history = json.loads(request.form["history"])
    interviewer = request.form["interviewer"]
    file = request.files["audio"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=app.config["UPLOAD_FOLDER"])
    file.save(tmp.name)

    # Whisper STT 日本語指定
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(tmp.name, "rb"),
        language="ja"
    )
    user_text = transcript.text

    # ChatGPT 次の質問生成（志望理由を含む履歴を維持）
    history.append({"role": "user", "content": user_text})
    chat_res = client.chat.completions.create(
        model="gpt-4",
        messages=history
    )
    next_q = chat_res.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": next_q})

    # TTS 生成 → Base64 で返却
    tts = client.audio.speech.create(
        model="tts-1",
        voice=SCRIPTS[interviewer]["voice"],
        input=next_q
    )
    import base64
    audio_b64 = base64.b64encode(tts.content).decode("ascii")

    return jsonify({
        "audio_base64": audio_b64,
        "next_question": next_q,
        "history": history
    })

#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=5000, debug=True)