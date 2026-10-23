# MA: The Voice Companion for New Mothers (Alexa+ & AWS Builder)

> **Tagline:** The ambient voice companion that cares for the mother, not just the baby.

---

## 💡 Inspiration

Every year, millions of new mothers bring their babies home from the hospital and enter a whirlwind of sleeplessness, hormonal upheaval, and isolation. While the app stores are flooded with baby trackers, nearly all of them treat the mother like an unpaid data-entry clerk—forcing her to log nursing milliliters, ounces, and diaper counts with bleary eyes at 3:00 AM. 

Worse still, traditional trackers induce tremendous guilt: *"Baby hasn't slept in 3 hours"*, *"Feeding duration below average"*.

**Nobody checks in on the mother.**

Postpartum depression (PPD) and anxiety affect 1 in 5 mothers globally, yet the majority suffer in silence. At 3:00 AM, in a dark nursery room, a mother doesn't want another spreadsheet. She needs a warm, compassionate presence that listens without judgment, logs her baby's natural rhythms hands-free, encourages her partner to take over chores, and gently acts as an intelligent safety net when she is overwhelmed.

That is why we built **MA** for **Alexa+**: an ambient voice companion designed from first principles to care for the mother.

---

## 🍼 What It Does

**MA** transforms the smart home into a supportive postpartum sanctuary through five core capabilities:

1. **Voice-First, Guilt-Free Companionship**:
   - Hands-free voice logging for breast feeds, bottles, and sleep stretches using natural language (*"Maya nursed for 15 minutes on the left side"* or *"Baby slept from 1pm to 2:30pm in her crib"*).
   - Zero guilt: No reminders that feeding was "too short" or naps were "irregular". All feeding choices (nursing, bottle, formula, solids) are validated equally.

2. **🌙 Night Mode by Design**:
   - Between 10:00 PM and 6:00 AM (or when activated), MA switches to **Night Mode**: all voice responses are strictly limited to **one short, soothing sentence**, and the UI eliminates all blue light ($\lambda < 500\,\text{nm}$) using a velvet plum and warm peach palette to preserve melatonin production.

3. **Family Teamwork & Partner Board**:
   - Postpartum care should never fall on one person. MA maintains a shared **Partner Support Board** (*"Sterilize evening bottles"*, *"Pick up diapers"*, *"Take the 4:00 AM shift so mom can sleep"*), empowering mothers to delegate tasks hands-free.

4. **Intelligent Safety & Distress Detection**:
   - Monitors emotional check-ins using mathematical pattern detection and NLP heuristics.
   - Detects postpartum despair, hopelessness, and **negated self-harm** (*"I'm not going to hurt myself, but everything is so dark"*—which traditional filters miss).
   - Immediately serves a non-alarming, empathetic care response connecting the mother to verified Indian helplines (**Tele-MANAS `14416`**, **Vandrevala Foundation `+91 9999 666 555`**) and encouraging contact with her doctor or midwife.

5. **SEP-1865 MCP Apps Interactive Cards**:
   - For screen-enabled devices like Echo Show, MA pairs tool calls with interactive HTML visual cards (`ui://` scheme) for baby rhythms, mood trends, and task checklists.

---

## 🛠️ How We Built It

MA is built on an open-standards, privacy-preserving decoupled architecture:

```
[ Mom's Voice / Web Simulator ]
             │
             ▼
[ FastAPI Agent Layer (:8001) ]  ◄──►  [ Amazon Bedrock (Claude 3.5 / Nova) ]
             │
      (Streamable HTTP)
             ▼
[ FastMCP Server (:8005 /mcp) ]  ◄──►  [ Local SQLite Database (ma.db) ]
             │
             ├── Typed Voice Tools (log_feed, log_sleep, baby_summary, etc.)
             ├── Safety Layer (India Helplines, Negation Catchers)
             └── SEP-1865 UI Cards (ui://ma/baby-summary-card)
```

### 1. Model Context Protocol (MCP) Streamable HTTP Transport
We implemented the official **MCP Specification (2025-11-25)**:
- Single unified endpoint at `/mcp` handling both `POST` (JSON-RPC 2.0 messages) and `GET` (resumption with `Last-Event-ID`).
- Stateful session management using the standard `MCP-Session-Id` HTTP header.
- Responses streamed via Server-Sent Events (`text/event-stream`) or single `application/json` payloads.

### 2. Amazon Bedrock & Strands Agents SDK
- **Amazon Bedrock Converse API**: Orchestrates high-empathy reasoning and multi-step tool selection using `anthropic.claude-3-5-sonnet` and `amazon.nova-lite`.
- **System Prompt Guardrails**: Enforces daytime brevity (1–2 sentences), Night Mode brevity (1 sentence), non-judgment, and medical non-advice rules.
- **Offline / Local Fallback**: Built an autonomous fallback execution loop that runs the full tool-use pipeline against the MCP server even when cloud credentials are unconfigured.

### 3. Mathematical Safety & Distress Thresholds
MA tracks wellness using rolling time-series calculations over historical check-ins:

$$\bar{S}_k = \frac{1}{k} \sum_{i=1}^k s_i$$

Where $s_i \in \{1, 2, 3, 4, 5\}$ represents the mother's subjective wellness score. MA triggers a proactive companion intervention when sustained depletion occurs:

$$\text{Trigger}_{\text{distress}} = \begin{cases} 
\text{True} & \text{if } \bar{S}_k \le 2.2 \quad (k \ge 3) \\ 
\text{True} & \text{if } \forall j \in \{0, 1, 2\}, \; s_{k-j} \le 2 \\
\text{True} & \text{if } \exists \, w \in \mathcal{K}_{\text{crisis}} \cup \mathcal{K}_{\text{negation}} \\
\text{False} & \text{otherwise}
\end{cases}$$

Where $\mathcal{K}_{\text{crisis}}$ and $\mathcal{K}_{\text{negation}}$ represent critical distress and negated self-harm lexicons.

### 4. Privacy-First Local SQLite Storage
All sensitive family logs—breastfeeding times, wake-ups, emotional check-ins, and notes—remain stored locally in `server/data/ma.db`. Personal maternal health data is never uploaded to third-party databases.

### 5. Swasth-Inspired Ambient Web Simulator
The frontend is styled with the warm maternal palette inspired by the **Swasth** platform:
- **Zero Blue**: Eliminated blue and cyan light entirely. Built with Swasth Rose (`#FF3B69`), Soft Peach (`#FFB088`), Warm Orchid (`#C084FC`), Mint (`#10B981`), and deep velvet berry obsidian (`#0B050E`).
- **Web Speech API**: Real-time browser speech recognition for hands-free voice input and speech synthesis for voice playback.
- **Live Tool Inspector**: Displays real-time JSON-RPC 2.0 requests, tool parameters, and server outputs as they execute.

---

## ⚡ Challenges We Faced

1. **Navigating the 2025-11-25 Streamable HTTP Specification**:
   Migrating from the legacy dual-endpoint HTTP+SSE design to the new unified `/mcp` Streamable HTTP transport required precise session lifecycle management (`MCP-Session-Id`), task group concurrency handling in Python's `anyio`, and origin validation to prevent DNS rebinding.

2. **Nuanced Maternal Distress vs. Normal Tiredness**:
   Every new mother is tired. A rule-based system that flags "I'm exhausted" as a mental health emergency would cause alarming false alarms. We carefully engineered a dual-layer classifier:
   - Routine exhaustion (*"tired from the 3am feed"*, score 3) receives empathetic companionship.
   - Acute postpartum despair (*"hopeless"*, *"failing my baby"*, *"can't do this anymore"*) or negated self-harm (*"I'm not going to hurt myself, but I want to disappear"*) immediately triggers the care response.

3. **Strict Voice-First Brevity**:
   LLMs naturally tend to produce verbose, multi-paragraph advice. In a dark nursery at 3:00 AM, hearing a 45-second lecture is stressful. We instituted strict sentence-boundary post-processors and system prompts enforcing the 1-sentence night rule.

4. **Browser Caching of Color Tokens**:
   Ensuring the new zero-blue Swasth color scheme loaded reliably across browsers required inlining critical CSS variables into the HTML head and utilizing cache-busting query strings.

---

## 🏆 Accomplishments That We're Proud Of

- **27/27 Automated Unit & Integration Tests Passing**: From natural time parsing (`1pm`, `2 hours ago`) to MCP Streamable HTTP handshakes and safety regressions.
- **Genuine Open Standards Compliance**: Full implementation of MCP Streamable HTTP (2025-11-25) and MCP Apps (SEP-1865 `ui://` resources).
- **Localized Care for Indian Mothers**: Configured with verified 24/7 hotlines including **Tele-MANAS (`14416`)**, **KIRAN (`1800-599-0019`)**, and the **Vandrevala Foundation (`+91 9999 666 555`)**.
- **A Product That Cares for the Caregiver**: Building something that respects the dignity, mental health, and physical exhaustion of new mothers.

---

## 📚 What We Learned

- **Decoupled Agentic Systems Are Superior**: Separating the MCP Tool/Resource server from the Agent reasoning layer makes tools reusable across Alexa+, web simulators, and custom LLM workflows without rewriting logic.
- **Voice UX Must Be Adaptive**: Daytime and nighttime voice assistants require fundamentally different conversational physics. Ambient interfaces must adapt their brevity, volume, and visual spectrum to the user's circadian environment.
- **Safety in Maternal Care Demands Caution**: Negations are a well-documented linguistic feature of suicidal and depressive ideation. Treating *"I'm not going to do anything stupid"* with compassionate care rather than ignoring it is essential in postpartum technology.

---

## 🚀 What's Next for MA

- **Acoustic Cry Analysis**: Integrating baby cry classification (hunger vs. gas vs. tiredness) to offer gentle suggestions during late-night crying bouts.
- **Wearable Sleep Integration**: Correlating maternal resting heart rate and HRV from smartwatches to proactively suggest when a partner should take the night shift.
- **Native Alexa+ Skill Deployment**: Packaging MA as a certified Alexa+ skill with custom Echo Show APL (Alexa Presentation Language) templates and multimodal widgets.
