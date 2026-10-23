# MA: The Voice Companion for New Mothers (Alexa+ & AWS Builder)

> **Tagline:** The ambient voice companion that cares for the mother, not just the baby.

---

## Inspiration

Every year, millions of new mothers enter the exhausting whirlwind of postpartum recovery. While app stores are flooded with baby trackers, nearly all of them treat mothers like unpaid data-entry clerks at 3:00 AM—forcing them to log nursing milliliters and sleep minutes into cold, bright spreadsheets.

Worse, traditional trackers induce guilt: *"Baby hasn't slept in 3 hours"*, *"Feeding duration below average"*.

**Nobody checks in on the mother.**

Postpartum depression and maternal depletion affect 1 in 5 mothers globally, yet most suffer in silence. At 3:00 AM in a dark nursery, a mother needs a warm, compassionate presence that listens without judgment, logs rhythms hands-free, encourages her partner to share the load, and acts as an intelligent safety net. We built **MA** to care for the caregiver.

---

## What it does

**MA** transforms the home into an ambient, hands-free maternal sanctuary across five core capabilities:

1. **Voice-First, Guilt-Free Companionship**:
   - Hands-free voice logging for nursing, bottle feeds, and sleep stretches using natural speech (*"Baby nursed 15 minutes on the left side"*).
   - Zero guilt: No rigid targets or alerts that feedings were "too short." All feeding and parenting choices are validated equally.

2. **🌙 Circadian Night Mode**:
   - Between 10:00 PM and 6:00 AM, MA automatically whispers in strictly **one short, soothing sentence** and eliminates all blue light ($\lambda < 500\,\text{nm}$) with a warm velvet plum palette to preserve infant and maternal melatonin.

3. **Smart Health & Wellness Toolkit**:
   - Interactive 40-week fetal growth visualizer with relatable fruit analogies.
   - Daily wellness trackers for hydration, prenatal vitamins, pelvic recovery, and a 10-kick countdown session.
   - Calming 432 Hz meditative audio and affirmations to reduce maternal cortisol during high-stress moments.

4. **Caregiver Circle & Partner Board**:
   - Keeps care from falling on one person by maintaining a shared partner task board (*"Sterilize night bottles"*, *"Take the 4:00 AM shift so mom can sleep"*).

5. **Intelligent Safety & Crisis Routing**:
   - Analyzes wellness trends and catches acute despair and **negated self-harm** (*"I'm not going to hurt myself, but I want to disappear"*).
   - Suppresses chit-chat to deliver immediate care responses connecting mothers to 24/7 maternal crisis lines and their doctor.

---

## How we built it

MA is built on a decoupled, privacy-first open architecture:

```
[ Mom's Voice / Ambient Device ]
               │
               ▼
 [ FastAPI Agent Layer (:8001) ]  ◄──►  [ Amazon Bedrock (Claude 3.5 / Nova) ]
               │
        (Streamable HTTP)
               ▼
 [ FastMCP Server (:8005 /mcp) ]  ◄──►  [ Encrypted Local SQLite (ma.db) ]
               │
               ├── Typed Voice Tools (log_feed, log_sleep, baby_summary, partner_tasks)
               ├── Deterministic Safety Layer (Crisis routing & negation catchers)
               └── Multimodal UI Cards (SEP-1865 ui:// resources for Echo Show)
```

- **Amazon Bedrock & Strands Agents SDK**: Orchestrates natural reasoning, tool execution, and enforces strict brevity guardrails (1–2 sentences daytime, 1 sentence night mode).
- **Model Context Protocol (MCP 2025-11-25)**: Streamable HTTP transport over a unified `/mcp` endpoint with stateful session management.
- **Mathematical Safety Scoring**: Proactively triggers non-diagnostic care when rolling wellness scores drop ($\bar{S}_k \le 2.2$) or crisis lexicons are detected:
  $$\bar{S}_k = \frac{1}{k} \sum_{i=1}^k s_i$$
- **Privacy-First Local Storage**: All family logs remain encrypted on-device in SQLite. Sensitive health data is never sold or uploaded to third-party databases.

---

## Challenges we ran into

1. **Normal Exhaustion vs. Acute Distress**: Every new mother is tired. We built a dual-layer classifier to separate everyday fatigue (*"exhausted from the 3am feed"*) from genuine postpartum depression and subtle negated self-harm.
2. **Suppressing LLM Verbosity**: LLMs tend to generate lengthy advice. We engineered deterministic boundary post-processors to enforce single-sentence brevity during midnight feeds.
3. **Migrating to MCP Streamable HTTP**: Transitioning from legacy SSE to the 2025-11-25 unified HTTP transport required precise session lifecycle management and task group concurrency in Python.

---

## Accomplishments that we're proud of

- **27/27 Automated Tests Passing**: Full test coverage across natural time parsing, Streamable HTTP handshakes, negation safety, and Bedrock agent contracts.
- **Voice-First Dignity**: A hands-free interface that never wakes a sleeping baby or makes an overwhelmed mother feel judged.
- **Open Standards Compliance**: Fully implemented MCP Streamable HTTP (2025-11-25) and MCP Apps (SEP-1865 visual cards).

---

## What we learned

- **Voice is an Accessibility Need**: When holding or nursing an infant, hands-free ambient voice isn't a novelty—it is essential.
- **Circadian Awareness Matters**: Day and night interactions require completely different conversational rules, volumes, and visual spectrums.
- **Decoupled Architecture Wins**: Separating the MCP tool server from the Bedrock agent allows the same core logic to run across smart speakers, smart displays, and companion apps effortlessly.

---

## What's next for Ma

- **Acoustic Cry Classification**: Distinguishing infant cries (hunger, gas, tiredness) to provide gentle suggestions during late-night crying bouts.
- **Wearable Recovery Sync**: Correlating maternal resting heart rate and sleep metrics from smartwatches to proactively suggest when partners should step in.
- **Certified Alexa+ Skill Deployment**: Packaging MA with custom Echo Show interactive widgets (APL) for smart home displays worldwide.
