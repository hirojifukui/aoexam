// フロント側の録音・再生・API通信ロジック
const step1 = document.getElementById("step1");
const step2 = document.getElementById("step2");
const step3 = document.getElementById("step3");
const motivationInput = document.getElementById("motivation");
const fileUpload = document.getElementById("fileUpload");
const btnNext = document.getElementById("btnNext");
const btnStart = document.getElementById("btnStart");
const interviewerSel = document.getElementById("interviewer");
const questionArea = document.getElementById("questionArea");
const btnPlayQ = document.getElementById("btnPlayQ");
const btnRecord = document.getElementById("btnRecord");
const btnStop = document.getElementById("btnStop");
const btnEnd = document.getElementById("btnEnd");
const player = document.getElementById("player");

let history = [];
let interviewerType = "";
let mediaRecorder, audioChunks = [];
let currentAudioURL = null;

// 各タイプの質問を事前取得するMap
const preQuestions = {};
const preHistories = {};

// ----------------------------
// Step1 → Step2
// ----------------------------
btnNext.onclick = async () => {
  // 志望理由テキスト取得
  const text = motivationInput.value || await (async () => {
    const f = fileUpload.files[0];
    return f ? new TextDecoder().decode(await f.arrayBuffer()) : "";
  })();

  step1.classList.add("hidden");
  step2.classList.remove("hidden");

  // インタビュアーごとに非同期に質問生成
  interviewerSel.querySelectorAll('option').forEach(opt => {
    const type = opt.value;
    fetch("/api/start", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({motivation: text, interviewer: type})
    })
    .then(res => res.json())
    .then(data => {
      preQuestions[type] = data.question;
      preHistories[type] = data.history;
    })
    .catch(err => {
      console.error('Pre-generation error for', type, err);
    });
  });
};

// ----------------------------
// Step2 → Start & Step3
// ----------------------------
btnStart.onclick = async () => {
  interviewerType = interviewerSel.value;
  step2.classList.add("hidden");
  step3.classList.remove("hidden");

  // 質問が生成されていない場合はローディング表示
  let question = preQuestions[interviewerType];
  let currentHistory = preHistories[interviewerType] || [];
  if (!question) {
    questionArea.innerText = "回答を吟味中…次の質問を検討中…";
    // 事前生成が間に合わなかった場合は改めて取得
    const res = await fetch("/api/start", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({motivation: motivationInput.value, interviewer: interviewerType})
    });
    const data = await res.json();
    question = data.question;
    history = data.history;
  } else {
    questionArea.innerText = question;
    history = currentHistory;
  }

  // 自動再生 (TTS)
  const ttsRes = await fetch("/api/tts", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ text: question, interviewer: interviewerType })
  });
  const ttsBlob = await ttsRes.blob();
  currentAudioURL = URL.createObjectURL(ttsBlob);
  player.src = currentAudioURL;
  player.hidden = false;
  player.play();
};

// ----------------------------
// 質問再生ボタン
// ----------------------------
btnPlayQ.onclick = () => {
  if (currentAudioURL) {
    player.src = currentAudioURL;
    player.hidden = false;
    player.play();
  }
};

// ----------------------------
// 録音開始
// ----------------------------
btnRecord.onclick = async () => {
  audioChunks = [];
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.start();
  btnRecord.disabled = true;
  btnStop.disabled = false;
};

// ----------------------------
// 録音停止 → STT → ChatGPT → TTS → 自動再生ループ
// ----------------------------
btnStop.onclick = async () => {
  mediaRecorder.stop();
  btnStop.disabled = true;
  btnRecord.disabled = false;
  questionArea.innerText = "回答を吟味中…次の質問を検討中…";  // ローディングメッセージ
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const form = new FormData();
    form.append("audio", audioBlob, "reply.webm");
    form.append("history", JSON.stringify(history));
    form.append("interviewer", interviewerType);

    const res = await fetch("/api/interview", { method: "POST", body: form });
    const data = await res.json();
    const { audio_base64, next_question, history: newHistory } = data;
    history = newHistory;

    questionArea.innerText = next_question;
    const audioSrc = "data:audio/mpeg;base64," + audio_base64;
    currentAudioURL = audioSrc;
    player.src = currentAudioURL;
    player.hidden = false;
    player.play();
  };
};

// ----------------------------
// 面接終了
// ----------------------------
btnEnd.onclick = () => {
  window.location.href = "/";
};
