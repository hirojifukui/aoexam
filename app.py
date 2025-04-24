import os
import json
import tempfile
from flask import Flask, request, render_template, jsonify, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 面接官タイプごとのプロンプトテンプレート読み込み
with open("interview_scripts.json", "r", encoding="utf-8") as f:
    SCRIPTS = json.load(f)

@app.route("/")
def index():
    return render_template("index.html", scripts=SCRIPTS)

@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.json
    text = data["motivation"]
    interviewer = data["interviewer"]
    # 初期履歴
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

@app.route("/api/interview", methods=["POST"])
def api_interview():
    """
    クライアントから渡された
    - history: これまでの会話履歴
    - audio: 音声ファイル（multipart/form-data）
    を受け取り、Whisperで文字起こし→ChatGPTで次質問生成→TTSで音声バイナリ返却
    """
    history = request.form.get("history")
    history = json.loads(history)
    # 音声ファイルを一時保存
    file = request.files["audio"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=app.config["UPLOAD_FOLDER"])
    file.save(tmp.name)

    # Whisperで文字起こし
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(tmp.name, "rb")
    )
    user_text = transcript.text

    # ChatGPTへ追加して次の質問生成
    history.append({"role": "user", "content": user_text})
    chat_res = client.chat.completions.create(
        model="gpt-4",
        messages=history
    )
    next_q = chat_res.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": next_q})

    # TTS生成
    tts = client.audio.speech.create(
        model="tts-1",
        voice=SCRIPTS[request.form["interviewer"]]["voice"],
        input=next_q
    )

    return (
        tts.content,
        200,
        {
            "Content-Type": "audio/mpeg",
            "X-Next-Question": next_q,
            "X-History": json.dumps(history),
        }
    )

if __name__ == "__main__":
    app.run(debug=True)
