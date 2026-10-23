/**
 * MA Alexa+ Simulator Client Script
 * - Voice Recognition (Web Speech API)
 * - Text-to-Speech (SpeechSynthesis)
 * - Live MCP Streamable HTTP Tool Call Inspector
 * - Baby Timeline & Partner Support Board
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
const chatFeed = document.getElementById("chatFeed");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const micBtn = document.getElementById("micBtn");
const ttsToggleBtn = document.getElementById("ttsToggleBtn");
const ttsIcon = document.getElementById("ttsIcon");
const nightModeBtn = document.getElementById("nightModeBtn");
const nightModeState = document.getElementById("nightModeState");
const partnerToggleBtn = document.getElementById("partnerToggleBtn");
const seedBtn = document.getElementById("seedBtn");

const alexaStage = document.querySelector(".alexa-stage");
const alexaStatus = document.getElementById("alexaStatus");

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
  initVoiceRecognition();
  setupEventListeners();
  loadBabyTimeline();
  loadPartnerTasks();
  checkMcpHealth();
});

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
  recognition.lang = "en-IN"; // Prioritize Indian English / global English

  recognition.onstart = () => {
    isRecognizing = true;
    micBtn.classList.add("active");
    alexaStage.classList.add("listening");
    alexaStatus.textContent = "Listening... Speak naturally to MA";
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
    alert("Speech recognition is not available in your browser. Please type your message.");
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
  micBtn.classList.remove("active");
  alexaStage.classList.remove("listening");
  alexaStatus.textContent = "Ready • Listening for voice or prompt";
}

// -------------------------------------------------------------
// Text-to-Speech (Web Speech Synthesis)
// -------------------------------------------------------------
function speakReply(text) {
  if (!isTtsEnabled || !("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel(); // Cancel any ongoing speech
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = isNightMode ? 0.9 : 1.0; // Slightly slower, softer in night mode
  utterance.pitch = 1.05;

  alexaStage.classList.add("speaking");
  alexaStatus.textContent = "Alexa+ speaking...";

  utterance.onend = () => {
    alexaStage.classList.remove("speaking");
    alexaStatus.textContent = "Ready • Listening for voice or prompt";
  };

  utterance.onerror = () => {
    alexaStage.classList.remove("speaking");
    alexaStatus.textContent = "Ready";
  };

  window.speechSynthesis.speak(utterance);
}

// -------------------------------------------------------------
// Chat Sending & Receiving
// -------------------------------------------------------------
async function sendMessage(text) {
  if (!text || !text.trim()) return;

  const userText = text.trim();
  appendUserMessage(userText);
  chatInput.value = "";

  alexaStatus.textContent = "Processing with Bedrock & MCP...";

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
    appendBotMessage(data);

    // Speak aloud
    speakReply(data.reply);

    // Handle tool calls
    if (data.tool_calls && data.tool_calls.length > 0) {
      data.tool_calls.forEach(tc => recordToolCall(tc));
      loadBabyTimeline();
      loadPartnerTasks();
    }

  } catch (err) {
    console.error("Chat error:", err);
    appendBotMessage({
      reply: "I'm having a little trouble connecting right now, mama. Let me take a breath and try again.",
      tool_calls: [],
      is_night_mode: isNightMode
    });
  } finally {
    if (!isRecognizing) {
      alexaStatus.textContent = "Ready • Listening for voice or prompt";
    }
  }
}

function appendUserMessage(text) {
  const msgEl = document.createElement("div");
  msgEl.className = "msg user";
  msgEl.innerHTML = `
    <div class="msg-avatar">You</div>
    <div class="msg-body">
      <p>${escapeHtml(text)}</p>
      <div class="msg-meta">Mom</div>
    </div>
  `;
  chatFeed.appendChild(msgEl);
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function appendBotMessage(data) {
  const msgEl = document.createElement("div");
  const isSafety = data.safety_triggered;
  msgEl.className = `msg bot ${isSafety ? "safety-card" : ""}`;

  let helplinesHtml = "";
  if (isSafety && data.helplines) {
    helplinesHtml = `
      <div class="safety-helpline-box">
        <strong>Direct Maternal Support & Crisis Numbers (India):</strong><br>
        • Tele-MANAS: <a href="tel:14416">14416</a> or <a href="tel:18008914416">1800-891-4416</a> (24/7 Toll-Free)<br>
        • Vandrevala Foundation: <a href="tel:+919999666555">+91 9999 666 555</a> (24/7 Counseling)<br>
        • Kiran Helpline: <a href="tel:18005990019">1800-599-0019</a>
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="msg-avatar">MA</div>
    <div class="msg-body">
      <p>${escapeHtml(data.reply)}</p>
      ${helplinesHtml}
      <div class="msg-meta">${data.is_night_mode ? "🌙 Night Mode (1 sentence)" : "☀️ Alexa+ Companion"}</div>
    </div>
  `;
  chatFeed.appendChild(msgEl);
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

// -------------------------------------------------------------
// Live MCP Tool Call Inspector
// -------------------------------------------------------------
function recordToolCall(tc) {
  toolCallCounter++;
  toolCallCount.textContent = `${toolCallCounter} call${toolCallCounter === 1 ? '' : 's'}`;

  // Remove empty state if present
  const emptyState = toolCallsStream.querySelector(".empty-state");
  if (emptyState) emptyState.remove();

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const card = document.createElement("div");
  card.className = "tool-call-card";
  card.innerHTML = `
    <div class="tool-header">
      <span class="tool-name">⚡ ${escapeHtml(tc.name)}</span>
      <span class="tool-time">${timeStr}</span>
    </div>
    <div style="font-size:0.7rem; color:var(--text-dim); margin-bottom:4px;">
      Args: <code>${escapeHtml(JSON.stringify(tc.args))}</code>
    </div>
    <pre class="tool-json">${escapeHtml(JSON.stringify(tc.result, null, 2))}</pre>
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
    // Read the UI resource from MCP server via POST /mcp resources/read
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
    
    // Extract list of feeds and sleeps from tool call result if available
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
        <div class="timeline-icon">🍼</div>
        <div class="timeline-details">
          <div><strong>${f.feed_type.replace('_', ' ')}</strong> • ${f.minutes_or_ml} ${f.feed_type.includes('breast') ? 'mins' : 'ml'}</div>
          <div class="timeline-time">${t} ${f.note ? '• ' + escapeHtml(f.note) : ''}</div>
        </div>
      </div>
    `;
  });

  sleeps.forEach(s => {
    const t = s.start_time ? s.start_time.split(" ")[1] : "Today";
    html += `
      <div class="timeline-event sleep-event">
        <div class="timeline-icon">💤</div>
        <div class="timeline-details">
          <div><strong>Sleep Interval</strong> • ${s.duration_minutes} mins</div>
          <div class="timeline-time">${t} ${s.note ? '• ' + escapeHtml(s.note) : ''}</div>
        </div>
      </div>
    `;
  });

  timelineContainer.innerHTML = html;
}

function renderDefaultTimeline() {
  timelineContainer.innerHTML = `
    <div class="timeline-event">
      <div class="timeline-icon">🍼</div>
      <div class="timeline-details">
        <div><strong>Breast Nursing</strong> • 20 mins (Right)</div>
        <div class="timeline-time">Today 3:30 AM • Night feed</div>
      </div>
    </div>
    <div class="timeline-event">
      <div class="timeline-icon">💤</div>
      <div class="timeline-details">
        <div><strong>Night Sleep</strong> • 2h 15m</div>
        <div class="timeline-time">12:45 AM - 3:00 AM • Long stretch</div>
      </div>
    </div>
    <div class="timeline-event">
      <div class="timeline-icon">🍼</div>
      <div class="timeline-details">
        <div><strong>Bottle Feed</strong> • 120 ml</div>
        <div class="timeline-time">Yesterday 8:30 PM • Formula</div>
      </div>
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
    }
  } catch (e) {
    // Fallback default tasks
    renderPartnerTasks([
      { id: 1, task: "Sterilize and prep evening bottles", assignee: "Alex", status: "pending" },
      { id: 2, task: "Pick up size 2 diapers from store", assignee: "Alex", status: "pending" },
      { id: 3, task: "Take 4:00 AM baby shift so mom sleeps", assignee: "Alex", status: "pending" },
      { id: 4, task: "Fold washed onesies", assignee: "Alex", status: "completed" }
    ]);
  }
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
        <span class="badge">${escapeHtml(t.assignee || 'Partner')}</span>
      </li>
    `;
  });

  partnerTaskList.innerHTML = html;
}

window.toggleTaskComplete = async function(id, checkbox) {
  const row = checkbox.closest(".task-row");
  row.classList.toggle("done", checkbox.checked);

  // Invoke tool via chat
  sendMessage(`complete partner task ${id}`);
};

// -------------------------------------------------------------
// Event Listeners & UI Helpers
// -------------------------------------------------------------
function setupEventListeners() {
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(chatInput.value);
  });

  micBtn.addEventListener("click", () => {
    if (isRecognizing) stopListening();
    else startListening();
  });

  ttsToggleBtn.addEventListener("click", () => {
    isTtsEnabled = !isTtsEnabled;
    ttsIcon.textContent = isTtsEnabled ? "🔊" : "🔇";
    ttsToggleBtn.title = isTtsEnabled ? "Voice Output: ON" : "Voice Output: OFF";
  });

  nightModeBtn.addEventListener("click", () => {
    isNightMode = !isNightMode;
    body.classList.toggle("night-mode", isNightMode);
    nightModeState.textContent = isNightMode ? "ON" : "OFF";
    alexaStatus.textContent = isNightMode 
      ? "🌙 Night Mode Active (1-sentence brevity for quiet nursery)" 
      : "☀️ Day Mode Active (1-2 sentences)";
  });

  partnerToggleBtn.addEventListener("click", () => {
    switchTab("partnerTab");
  });

  seedBtn.addEventListener("click", async () => {
    if (confirm("Reset database with fresh 5-day realistic demo data for baby Maya?")) {
      seedBtn.disabled = true;
      seedBtn.textContent = "Resetting...";
      try {
        await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: "today summary" })
        });
        loadBabyTimeline();
        loadPartnerTasks();
        alert("Demo data refreshed!");
      } finally {
        seedBtn.disabled = false;
        seedBtn.innerHTML = `<span class="icon">🔄</span><span class="btn-text">Reset Demo Baby</span>`;
      }
    }
  });

  refreshTimelineBtn.addEventListener("click", () => {
    loadBabyTimeline();
  });

  addTaskForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const taskText = newTaskInput.value.trim();
    if (taskText) {
      sendMessage(`assign partner task: ${taskText}`);
      newTaskInput.value = "";
    }
  });

  // Prompt chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      chatInput.value = prompt;
      sendMessage(prompt);
    });
  });

  // Panel tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  const targetContent = document.getElementById(tabId);
  if (targetBtn) targetBtn.classList.add("active");
  if (targetContent) targetContent.classList.add("active");
}

async function checkMcpHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.querySelector("#mcpStatus .status-label").textContent = "MCP :8000 (Connected)";
    }
  } catch (e) {
    document.querySelector("#mcpStatus .status-dot").classList.remove("online");
    document.querySelector("#mcpStatus .status-label").textContent = "MCP Offline (Start server)";
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
