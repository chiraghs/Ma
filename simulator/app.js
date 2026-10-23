/**
 * MA Alexa+ Smart Display Device Simulator (Echo Show 10)
 * - Echo Show Screen State Machine (Ambient Home vs. Active Voice/APL)
 * - Voice Input (Web Speech API) & Push-to-Talk Echo Button
 * - Speech Synthesis (Alexa Voice Output with Circadian Night Speed)
 * - The Iconic Alexa Multimodal Light Bar
 * - Live MCP Streamable HTTP Tool Telemetry Drawer
 * - SEP-1865 MCP Apps Sandboxed Iframe Bridge
 */

const API_BASE = window.location.origin.includes(":8001") 
  ? window.location.origin 
  : "http://127.0.0.1:8001";

const MCP_SERVER_URL = "http://127.0.0.1:8005/mcp";

// State
let isNightMode = false;
let isTtsEnabled = true;
let toolCallCounter = 0;
let recognition = null;
let isRecognizing = false;

// DOM Elements
const body = document.body;
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const micBtn = document.getElementById("micBtn");
const ttsToggleBtn = document.getElementById("ttsToggleBtn");
const ttsIcon = document.getElementById("ttsIcon");
const nightModeBtn = document.getElementById("nightModeBtn");
const nightModeState = document.getElementById("nightModeState");
const partnerToggleBtn = document.getElementById("partnerToggleBtn");
const telemetryToggleBtn = document.getElementById("telemetryToggleBtn");
const telemetryDrawer = document.getElementById("telemetryDrawer");
const closeTelemetryBtn = document.getElementById("closeTelemetryBtn");
const seedBtn = document.getElementById("seedBtn");

// Echo Show Screen Views
const ambientHomeView = document.getElementById("ambientHomeView");
const activeVoiceView = document.getElementById("activeVoiceView");
const userCaptionText = document.getElementById("userCaptionText");
const alexaResponseText = document.getElementById("alexaResponseText");
const brevityTag = document.getElementById("brevityTag");
const safetyBanner = document.getElementById("safetyBanner");
const helplineBadges = document.getElementById("helplineBadges");
const alexaLightBar = document.getElementById("alexaLightBar");
const alexaStatus = document.getElementById("alexaStatus");
const deviceClock = document.getElementById("deviceClock");
const greetingTime = document.getElementById("greetingTime");

// Telemetry & Inspector
const toolCallsStream = document.getElementById("toolCallsStream");
const toolCallCount = document.getElementById("toolCallCount");
const timelineContainer = document.getElementById("timelineContainer");
const refreshTimelineBtn = document.getElementById("refreshTimelineBtn");
const partnerTaskList = document.getElementById("partnerTaskList");
const pendingTaskCount = document.getElementById("pendingTaskCount");
const addTaskForm = document.getElementById("addTaskForm");
const newTaskInput = document.getElementById("newTaskInput");

const mcpAppPreviewContainer = document.getElementById("mcpAppPreviewContainer");
const previewUri = document.getElementById("previewUri");
const mcpAppIframe = document.getElementById("mcpAppIframe");

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initLiveClock();
  initVoiceRecognition();
  setupEventListeners();
  loadBabyTimeline();
  loadPartnerTasks();
  checkMcpHealth();
});

// -------------------------------------------------------------
// Live Device Clock & Greeting
// -------------------------------------------------------------
function initLiveClock() {
  function updateTime() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    const displayHours = hours % 12 || 12;
    if (deviceClock) {
      deviceClock.textContent = `${displayHours}:${minutes} ${ampm}`;
    }

    if (greetingTime) {
      if (hours >= 22 || hours < 5) greetingTime.textContent = "Good Night";
      else if (hours < 12) greetingTime.textContent = "Good Morning";
      else if (hours < 17) greetingTime.textContent = "Good Afternoon";
      else greetingTime.textContent = "Good Evening";
    }
  }
  updateTime();
  setInterval(updateTime, 1000);
}

// -------------------------------------------------------------
// Voice Recognition (Web Speech API)
// -------------------------------------------------------------
function initVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micBtn.title = "Speech recognition not supported in this browser. Please type.";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isRecognizing = true;
    micBtn.classList.add("recording");
    alexaLightBar.style.boxShadow = "0 0 25px #FF3B69, 0 0 45px #FFB088";
    alexaStatus.textContent = "Alexa is listening... Speak naturally";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    sendMessage(transcript);
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    stopListening();
  };

  recognition.onend = () => {
    stopListening();
  };
}

function startListening() {
  if (!recognition) {
    alert("Speech recognition is not available in your browser. Please type your voice prompt below.");
    return;
  }
  try {
    recognition.start();
  } catch (e) {
    recognition.stop();
  }
}

function stopListening() {
  isRecognizing = false;
  micBtn.classList.remove("recording");
  alexaLightBar.style.boxShadow = "0 0 16px rgba(255, 59, 105, 0.7)";
  alexaStatus.textContent = "Alexa is ready • Tap mic or speak";
}

// -------------------------------------------------------------
// Text-to-Speech (Web Speech Synthesis)
// -------------------------------------------------------------
function speakReply(text) {
  if (!isTtsEnabled || !("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = isNightMode ? 0.88 : 1.0;
  utterance.pitch = 1.05;

  alexaStatus.textContent = "MA is speaking on Echo Show...";
  alexaLightBar.style.boxShadow = "0 0 30px #FF3B69, 0 0 50px #C084FC";

  utterance.onend = () => {
    alexaLightBar.style.boxShadow = "0 0 16px rgba(255, 59, 105, 0.7)";
    alexaStatus.textContent = "Alexa is ready • Tap mic or speak";
  };

  utterance.onerror = () => {
    alexaStatus.textContent = "Alexa is ready";
  };

  window.speechSynthesis.speak(utterance);
}

// -------------------------------------------------------------
// Voice Command Execution & Screen State Transition
// -------------------------------------------------------------
async function sendMessage(text) {
  if (!text || !text.trim()) return;

  const userText = text.trim();
  chatInput.value = "";

  // Switch Echo Show Screen to Active Voice View
  ambientHomeView.style.display = "none";
  activeVoiceView.style.display = "flex";
  userCaptionText.textContent = `"${userText}"`;
  alexaResponseText.textContent = "Listening and reasoning with Amazon Bedrock & MCP...";
  safetyBanner.style.display = "none";
  brevityTag.textContent = isNightMode ? "🌙 Night Mode: 1 Sentence" : "1–2 Sentences";
  alexaStatus.textContent = "Bedrock Converse reasoning over MCP...";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userText,
        is_night_mode: isNightMode
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    renderEchoResponse(data);

    // Speak aloud
    speakReply(data.reply);

    // Handle tool calls
    if (data.tool_calls && data.tool_calls.length > 0) {
      data.tool_calls.forEach(tc => recordToolCall(tc));
      loadBabyTimeline();
      loadPartnerTasks();
    }

  } catch (err) {
    console.warn("Backend not reachable (offline/static mode). Running client companion engine:", err);
    const fallbackData = generateClientFallback(userText, isNightMode);
    renderEchoResponse(fallbackData);
    speakReply(fallbackData.reply);

    if (fallbackData.tool_calls && fallbackData.tool_calls.length > 0) {
      fallbackData.tool_calls.forEach(tc => recordToolCall(tc));
      loadBabyTimeline();
      loadPartnerTasks();
    }
  } finally {
    if (!isRecognizing) {
      alexaStatus.textContent = "Alexa is ready • Tap mic or speak";
    }
  }
}

function renderEchoResponse(data) {
  alexaResponseText.textContent = data.reply;
  brevityTag.textContent = data.is_night_mode ? "🌙 Night Mode: 1 Sentence" : "1–2 Sentences";

  // Check if distress / safety triggered
  if (data.safety_triggered) {
    safetyBanner.style.display = "flex";
    helplineBadges.innerHTML = "";
    const lines = data.helplines || [
      { name: "Tele-MANAS", number: "14416" },
      { name: "Vandrevala Crisis Line", number: "+91 9999 666 555" },
      { name: "Maternal Mental Health", number: "1-833-852-6262" }
    ];
    lines.forEach(h => {
      const b = document.createElement("span");
      b.className = "helpline-badge";
      b.textContent = `${h.name}: ${h.number}`;
      helplineBadges.appendChild(b);
    });
  } else {
    safetyBanner.style.display = "none";
  }
}

// -------------------------------------------------------------
// Live MCP Tool Call Inspector
// -------------------------------------------------------------
function recordToolCall(tc) {
  toolCallCounter++;
  toolCallCount.textContent = `${toolCallCounter} call${toolCallCounter > 1 ? 's' : ''}`;

  const emptyState = toolCallsStream.querySelector(".empty-state");
  if (emptyState) emptyState.remove();

  const card = document.createElement("div");
  card.className = "tool-call-card";
  card.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <span class="tool-name">⚡ ${escapeHtml(tc.name)}</span>
      <span class="tool-status">200 OK • JSON-RPC</span>
    </div>
    <div class="tool-params"><strong>Params:</strong> <code>${escapeHtml(JSON.stringify(tc.args))}</code></div>
    <div class="tool-output"><strong>Result:</strong> <code>${escapeHtml(JSON.stringify(tc.result))}</code></div>
  `;
  toolCallsStream.prepend(card);

  // Check if tool returned SEP-1865 _meta.ui.resourceUri
  const metaUi = tc.result?._meta?.ui;
  if (metaUi && metaUi.resourceUri) {
    loadMcpAppUi(metaUi.resourceUri);
  }
}

// -------------------------------------------------------------
// SEP-1865 MCP Apps UI Rendering
// -------------------------------------------------------------
async function loadMcpAppUi(resourceUri) {
  try {
    const res = await fetch(MCP_SERVER_URL, {
      method: "POST",
      headers: {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method: "resources/read",
        params: { uri: resourceUri }
      })
    });

    const data = await res.json();
    let htmlContent = "";
    if (data?.result?.contents?.[0]?.text) {
      htmlContent = data.result.contents[0].text;
    }

    if (htmlContent) {
      previewUri.textContent = resourceUri;
      mcpAppPreviewContainer.style.display = "block";
      mcpAppIframe.srcdoc = htmlContent;
    }
  } catch (err) {
    console.warn("Could not load MCP App resource:", err);
  }
}

// -------------------------------------------------------------
// Baby Timeline Loader (SQLite Direct via Agent)
// -------------------------------------------------------------
async function loadBabyTimeline() {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "today summary" })
    });
    const data = await res.json();
    const summaryCall = data.tool_calls?.find(c => c.name === "baby_summary");
    if (summaryCall && summaryCall.result) {
      renderTimeline(summaryCall.result);
    } else {
      renderDefaultTimeline();
    }
  } catch (e) {
    renderDefaultTimeline();
  }
}

function renderTimeline(res) {
  const feeds = res.feeds_list || [];
  const sleeps = res.sleeps_list || [];
  
  if (feeds.length === 0 && sleeps.length === 0) {
    timelineContainer.innerHTML = `<div class="empty-state">No events recorded today yet.</div>`;
    return;
  }

  let html = "";
  feeds.forEach(f => {
    const t = f.logged_at ? f.logged_at.split(" ")[1] : "Today";
    html += `
      <div class="timeline-event">
        <div style="font-weight:700; color:#FF3B69;">🍼 ${f.feed_type.replace('_', ' ')} • ${f.minutes_or_ml} ${f.feed_type.includes('breast') ? 'mins' : 'ml'}</div>
        <div style="font-size:11px; opacity:0.8;">${t} ${f.note ? '• ' + escapeHtml(f.note) : ''}</div>
      </div>
    `;
  });

  sleeps.forEach(s => {
    const t = s.start_time ? s.start_time.split(" ")[1] : "Today";
    html += `
      <div class="timeline-event sleep-event">
        <div style="font-weight:700; color:#C084FC;">💤 Sleep Stretch • ${s.duration_minutes} mins</div>
        <div style="font-size:11px; opacity:0.8;">${t} ${s.note ? '• ' + escapeHtml(s.note) : ''}</div>
      </div>
    `;
  });

  timelineContainer.innerHTML = html;
}

function renderDefaultTimeline() {
  timelineContainer.innerHTML = `
    <div class="timeline-event">
      <div style="font-weight:700; color:#FF3B69;">🍼 Nursing • 15 mins (Left side)</div>
      <div style="font-size:11px; opacity:0.8;">3:15 AM • Night nurse</div>
    </div>
    <div class="timeline-event sleep-event">
      <div style="font-weight:700; color:#C084FC;">💤 Crib Sleep • 135 mins</div>
      <div style="font-size:11px; opacity:0.8;">12:45 AM - 3:00 AM • Long stretch</div>
    </div>
    <div class="timeline-event">
      <div style="font-weight:700; color:#FF3B69;">🍼 Bottle Feed • 120 ml</div>
      <div style="font-size:11px; opacity:0.8;">Yesterday 8:30 PM • Formula</div>
    </div>
  `;
}

// -------------------------------------------------------------
// Partner Support Tasks
// -------------------------------------------------------------
async function loadPartnerTasks() {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "list partner tasks" })
    });
    const data = await res.json();
    const taskCall = data.tool_calls?.find(c => c.name === "partner_tasks");
    if (taskCall && taskCall.result && taskCall.result.tasks) {
      renderPartnerTasks(taskCall.result.tasks);
    } else {
      renderDefaultPartnerTasks();
    }
  } catch (e) {
    renderDefaultPartnerTasks();
  }
}

function renderDefaultPartnerTasks() {
  renderPartnerTasks([
    { id: 1, task: "Sterilize and prep evening bottles", assignee: "Alex", status: "pending" },
    { id: 2, task: "Pick up size 2 diapers from store", assignee: "Alex", status: "pending" },
    { id: 3, task: "Take 4:00 AM baby shift so mom sleeps", assignee: "Alex", status: "pending" },
    { id: 4, task: "Fold washed onesies", assignee: "Alex", status: "completed" }
  ]);
}

function renderPartnerTasks(tasks) {
  const pending = tasks.filter(t => t.status === "pending");
  pendingTaskCount.textContent = `${pending.length} pending`;

  let html = "";
  tasks.forEach(t => {
    const isDone = t.status === "completed";
    html += `
      <li class="task-row ${isDone ? 'done' : ''}">
        <div style="display:flex; align-items:center; gap:8px;">
          <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleTaskComplete(${t.id}, this)">
          <span>${escapeHtml(t.task)}</span>
        </div>
        <span style="font-size:11px; color:#FF8BA7;">${escapeHtml(t.assignee || 'Partner')}</span>
      </li>
    `;
  });
  partnerTaskList.innerHTML = html;
}

window.toggleTaskComplete = async function(taskId, checkbox) {
  const isDone = checkbox.checked;
  const row = checkbox.closest(".task-row");
  if (isDone) row.classList.add("done");
  else row.classList.remove("done");

  try {
    await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: `complete partner task ${taskId}` })
    });
  } catch (e) {
    console.warn("Could not sync task complete:", e);
  }
};

// -------------------------------------------------------------
// Setup Event Listeners
// -------------------------------------------------------------
function setupEventListeners() {
  // Push-to-Talk Button
  micBtn.addEventListener("click", () => {
    if (isRecognizing) stopListening();
    else startListening();
  });

  // Utterance Form Submission
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(chatInput.value);
  });

  // "Things to Try" Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt) sendMessage(prompt);
    });
  });

  // Night Mode Toggle (Circadian & Zero Blue)
  nightModeBtn.addEventListener("click", () => {
    isNightMode = !isNightMode;
    if (isNightMode) {
      body.classList.remove("day-mode");
      body.classList.add("night-mode");
      nightModeState.textContent = "ON";
      nightModeBtn.style.background = "#FFB088";
      nightModeBtn.style.color = "#16080D";
    } else {
      body.classList.remove("night-mode");
      body.classList.add("day-mode");
      nightModeState.textContent = "OFF";
      nightModeBtn.style.background = "rgba(255, 59, 105, 0.14)";
      nightModeBtn.style.color = "#FF8BA7";
    }
  });

  // Partner Screen View Toggle
  partnerToggleBtn.addEventListener("click", () => {
    telemetryDrawer.classList.toggle("open");
    switchTelemetryTab("partnerTab");
  });

  // Telemetry Drawer Toggle
  if (telemetryToggleBtn) {
    telemetryToggleBtn.addEventListener("click", () => {
      telemetryDrawer.classList.toggle("open");
    });
  }
  if (closeTelemetryBtn) {
    closeTelemetryBtn.addEventListener("click", () => {
      telemetryDrawer.classList.remove("open");
    });
  }

  // Telemetry Tab Switchers
  document.querySelectorAll(".telemetry-tabs .tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTelemetryTab(tabId);
    });
  });

  // Reset Demo Data
  seedBtn.addEventListener("click", async () => {
    seedBtn.disabled = true;
    seedBtn.textContent = "Resetting...";
    try {
      await fetch(`${API_BASE}/seed`, { method: "POST" });
    } catch(e) {}
    loadBabyTimeline();
    loadPartnerTasks();
    seedBtn.disabled = false;
    seedBtn.innerHTML = `<span class="icon">🔄</span><span class="btn-text">Reset Demo</span>`;
  });

  // Add Partner Task
  addTaskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const task = newTaskInput.value.trim();
    if (!task) return;
    newTaskInput.value = "";
    sendMessage(`add partner task ${task}`);
  });
}

function switchTelemetryTab(tabId) {
  document.querySelectorAll(".telemetry-tabs .tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".telemetry-drawer .tab-content").forEach(c => c.classList.remove("active"));

  const targetBtn = document.querySelector(`.telemetry-tabs .tab-btn[data-tab="${tabId}"]`);
  const targetContent = document.getElementById(tabId);
  if (targetBtn) targetBtn.classList.add("active");
  if (targetContent) targetContent.classList.add("active");
}

async function checkMcpHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.querySelector("#mcpStatus .status-label").textContent = "MCP :8005 (Streamable HTTP)";
    }
  } catch (e) {
    document.querySelector("#mcpStatus .status-dot").classList.remove("online");
    document.querySelector("#mcpStatus .status-label").textContent = "MCP Local (Autonomous)";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// -------------------------------------------------------------
// Autonomous Client-Side Companion Fallback (Static Hosting / Offline)
// -------------------------------------------------------------
function generateClientFallback(userText, isNight) {
  const text = userText.toLowerCase();

  // 1. Safety & Distress triggers
  const crisisWords = ["hopeless", "can't do this anymore", "failing", "want to die", "hurt myself", "disappear", "harm myself", "hate myself", "not going to hurt myself"];
  const isCrisis = crisisWords.some(w => text.includes(w));
  if (isCrisis) {
    return {
      reply: "Sarah, you are carrying so much, and you are not alone. Please reach out to your doctor or midwife, or call a trusted 24/7 careline today. We are right here with you.",
      safety_triggered: true,
      helplines: [
        { name: "Tele-MANAS", number: "14416" },
        { name: "Vandrevala Foundation", number: "+91 9999 666 555" },
        { name: "Maternal Mental Health", number: "1-833-852-6262" }
      ],
      tool_calls: [{
        name: "mood_checkin",
        args: { score: 1, note: userText },
        result: { status: "logged", care_response: true, _meta: { ui: { resourceUri: "ui://ma/mood-trend-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 2. Feeding
  if (text.includes("feed") || text.includes("nurse") || text.includes("bottle") || text.includes("nursed") || text.includes("ml")) {
    const isBottle = text.includes("bottle") || text.includes("ml");
    const reply = isNight
      ? "Logged Maya's feed. Rest your eyes now, mama."
      : "I've logged Maya's feeding session. You're doing a wonderful job keeping her nourished.";
    return {
      reply,
      tool_calls: [{
        name: "log_feed",
        args: { feed_type: isBottle ? "bottle" : "breast_left", minutes_or_ml: isBottle ? 120 : 15, note: "Autonomous client log" },
        result: { status: "logged", _meta: { ui: { resourceUri: "ui://ma/baby-summary-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 3. Sleep
  if (text.includes("sleep") || text.includes("slept") || text.includes("nap") || text.includes("bed") || text.includes("crib")) {
    const reply = isNight
      ? "Maya's sleep is logged. Try to get some quiet rest."
      : "Logged Maya's rest stretch. Make sure to rest your feet while you can, Sarah.";
    return {
      reply,
      tool_calls: [{
        name: "log_sleep",
        args: { start_time: "1:00 PM", end_time: "2:30 PM", duration_minutes: 90 },
        result: { status: "logged", duration_minutes: 90, _meta: { ui: { resourceUri: "ui://ma/baby-summary-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 4. Summary / Day
  if (text.includes("summary") || text.includes("today") || text.includes("day") || text.includes("how has")) {
    const reply = isNight
      ? "Maya had 5 feeds and 4 peaceful rest stretches today."
      : "Today Maya has had 5 feedings and 4 rest stretches totaling 6 hours. You're caring for her beautifully.";
    return {
      reply,
      tool_calls: [{
        name: "baby_summary",
        args: { period: "today" },
        result: { feeds_count: 5, total_sleep_hours: 6.0, status: "healthy", _meta: { ui: { resourceUri: "ui://ma/baby-summary-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 5. Partner / Tasks
  if (text.includes("partner") || text.includes("task") || text.includes("chore") || text.includes("alex")) {
    const reply = isNight
      ? "Task added to your partner's support board."
      : "I've added that to your partner support board so you don't have to carry everything alone.";
    return {
      reply,
      tool_calls: [{
        name: "partner_tasks",
        args: { action: "assign", task: userText, assignee: "Alex" },
        result: { status: "assigned", _meta: { ui: { resourceUri: "ui://ma/partner-tasks-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 6. Mood / Exhaustion
  if (text.includes("exhaust") || text.includes("tired") || text.includes("mood") || text.includes("feel")) {
    const reply = isNight
      ? "You're carrying so much tonight. Please close your eyes and rest."
      : "I hear how exhausted you are, Sarah. Postpartum recovery takes real time. Please be gentle with yourself today.";
    return {
      reply,
      tool_calls: [{
        name: "mood_checkin",
        args: { score: 2, note: userText },
        result: { status: "logged", _meta: { ui: { resourceUri: "ui://ma/mood-trend-card" } } }
      }],
      is_night_mode: isNight
    };
  }

  // 7. Medical query
  if (text.includes("calpol") || text.includes("medicine") || text.includes("dose") || text.includes("fever") || text.includes("doctor")) {
    return {
      reply: "Please check with your pediatrician or healthcare provider for all medication dosages and baby fever guidelines.",
      is_night_mode: isNight,
      tool_calls: []
    };
  }

  // Default companion response
  return {
    reply: isNight 
      ? "I'm right here with you, Sarah." 
      : "I'm listening, Sarah. You and Maya are doing wonderfully today.",
    is_night_mode: isNight,
    tool_calls: []
  };
}
