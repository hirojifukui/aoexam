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

// Step1 → Step2
btnNext.onclick = () => {
  step1.classList.add("hidden");
  step2.classList.remove("hidden");
};

// Step2 → API / 面接開始 → Step3
btnStart.onclick = async () => {
  interviewerType = interviewerSel.value;
  const text = motivationInput.value ||
               await (async () => {
                 const f = fileUpload.files[0];
                 return f ? new TextDecoder().decode(await f.arrayBuffer()) : "";
               })();

  const res = await fetch("/api/start", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({motivation: text, interviewer: interviewerType})
  });
  const {question, history: h} = await res.json();
  history = h;
  questionArea.innerText = question;
  step2.classList.add("hidden");
  step3.classList.remove("hidden");
};

// 質問再生（TTS → audio.player）
btnPlayQ.onclick = async () => {
  const res = await fetch("/api/interview", {
    method: "POST",
    body: new FormData(Object.assign(new FormData(), {
      history: JSON.stringify(history),
      interviewer: interviewerType
    }))
  });
  const blob = await res.blob();
  const nextQ = res.headers.get("X-Next-Question");
  history = JSON.parse(res.headers.get("X-History"));

  player.src = URL.createObjectURL(blob);
  player.hidden = false;
  questionArea.innerText = nextQ;
  player.play();
};

// 録音開始
btnRecord.onclick = async () => {
  audioChunks = [];
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.start();
  btnRecord.disabled = true;
  btnStop.disabled = false;
};

// 録音停止 → Whisper/STT & 次質問生成
btnStop.onclick = async () => {
  mediaRecorder.stop();
  btnStop.disabled = true;
  btnRecord.disabled = false;
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const form = new FormData();
    form.append("audio", audioBlob, "reply.webm");
    form.append("history", JSON.stringify(history));
    form.append("interviewer", interviewerType);

    // Whisper→ChatGPT→TTS を /api/interview に一気に投げる
    const res = await fetch("/api/interview", { method: "POST", body: form });
    const audioResp = await res.blob();
    const nextQ = res.headers.get("X-Next-Question");
    history = JSON.parse(res.headers.get("X-History"));

    // 再生
    player.src = URL.createObjectURL(audioResp);
    player.hidden = false;
    questionArea.innerText = nextQ;
    player.play();
  };
};

// 終了して最初に戻る
btnEnd.onclick = () => {
  window.location.href = "/";
};
