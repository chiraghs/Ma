"""
MCP Apps UI Resources (SEP-1865: Interactive User Interfaces for MCP)
Provides HTML templates declared with the `ui://` URI scheme and MIME type
`text/html;profile=mcp-app`. These render as sandboxed cards in the Alexa+ interface.
"""

BABY_SUMMARY_CARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA Baby Summary</title>
  <style>
    :root {
      --bg: #121824;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.1);
      --accent-cyan: #00e5ff;
      --accent-pink: #ff77a9;
      --accent-lavender: #b388ff;
      --text: #f0f4f8;
      --text-muted: #94a3b8;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 16px;
      box-sizing: border-box;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--card-border);
    }
    .title {
      font-size: 16px;
      font-weight: 600;
      color: var(--accent-cyan);
      letter-spacing: 0.5px;
    }
    .badge {
      font-size: 12px;
      padding: 3px 8px;
      background: rgba(0, 229, 255, 0.15);
      border-radius: 12px;
      color: var(--accent-cyan);
    }
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 16px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 12px;
      text-align: center;
    }
    .stat-val {
      font-size: 22px;
      font-weight: 700;
      margin-top: 4px;
      color: #fff;
    }
    .stat-lbl {
      font-size: 11px;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.5px;
    }
    .timeline {
      margin-top: 14px;
    }
    .timeline-title {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 10px;
      color: var(--text-muted);
    }
    .timeline-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      margin-bottom: 6px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
      border-left: 3px solid var(--accent-cyan);
      font-size: 13px;
    }
    .timeline-item.sleep {
      border-left-color: var(--accent-lavender);
    }
    .time {
      font-size: 11px;
      color: var(--text-muted);
      min-width: 55px;
    }
    .desc {
      flex: 1;
    }
  </style>
</head>
<body>
  <div class="header">
    <span class="title">👶 Baby Maya's Day</span>
    <span class="badge" id="periodBadge">Recent</span>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-lbl">Total Feeds</div>
      <div class="stat-val" id="totalFeeds">6</div>
    </div>
    <div class="stat-card">
      <div class="stat-lbl">Total Sleep</div>
      <div class="stat-val" id="totalSleep">12.5 hrs</div>
    </div>
  </div>

  <div class="timeline">
    <div class="timeline-title">Recent Rhythm</div>
    <div id="timelineList">
      <div class="timeline-item">
        <span class="time">Just now</span>
        <span class="desc">🍼 Bottle Feed • 120ml</span>
      </div>
      <div class="timeline-item sleep">
        <span class="time">1:30 PM</span>
        <span class="desc">💤 Nap • 1h 45m</span>
      </div>
      <div class="timeline-item">
        <span class="time">11:00 AM</span>
        <span class="desc">🤱 Breastfeed • Left 15m</span>
      </div>
    </div>
  </div>

  <script>
    // Listen for data updates via postMessage from host (SEP-1865)
    window.addEventListener('message', (event) => {
      const data = event.data;
      if (data && data.type === 'UPDATE_DATA') {
        if (data.period) document.getElementById('periodBadge').textContent = data.period;
        if (data.totalFeeds !== undefined) document.getElementById('totalFeeds').textContent = data.totalFeeds;
        if (data.totalSleep !== undefined) document.getElementById('totalSleep').textContent = data.totalSleep;
      }
    });

    // Notify host that UI app is ready
    if (window.parent) {
      window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, '*');
    }
  </script>
</body>
</html>
"""

MOOD_TREND_CARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA Mood & Rest Trend</title>
  <style>
    :root {
      --bg: #121824;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.1);
      --accent: #ff77a9;
      --accent-cyan: #00e5ff;
      --text: #f0f4f8;
      --text-muted: #94a3b8;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 16px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .title {
      font-size: 15px;
      font-weight: 600;
      color: var(--accent);
    }
    .chart {
      display: flex;
      align-items: flex-end;
      gap: 10px;
      height: 100px;
      padding: 10px 0;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 12px;
    }
    .bar-group {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }
    .bar {
      width: 100%;
      background: linear-gradient(180deg, var(--accent), rgba(255, 119, 169, 0.3));
      border-radius: 4px 4px 0 0;
      min-height: 10px;
      transition: height 0.4s ease;
    }
    .day-lbl {
      font-size: 11px;
      color: var(--text-muted);
    }
    .note-box {
      background: rgba(255, 119, 169, 0.1);
      border: 1px solid rgba(255, 119, 169, 0.2);
      border-radius: 8px;
      padding: 10px;
      font-size: 12px;
      line-height: 1.4;
      color: #ffd1dc;
    }
  </style>
</head>
<body>
  <div class="header">
    <span class="title">🌸 Mother's Wellness Trend</span>
    <span style="font-size: 12px; color: var(--text-muted);">Last 5 Days</span>
  </div>

  <div class="chart">
    <div class="bar-group">
      <div class="bar" style="height: 80%;"></div>
      <span class="day-lbl">Mon</span>
    </div>
    <div class="bar-group">
      <div class="bar" style="height: 80%;"></div>
      <span class="day-lbl">Tue</span>
    </div>
    <div class="bar-group">
      <div class="bar" style="height: 60%;"></div>
      <span class="day-lbl">Wed</span>
    </div>
    <div class="bar-group">
      <div class="bar" style="height: 40%; background: #fb7185;"></div>
      <span class="day-lbl">Thu</span>
    </div>
    <div class="bar-group">
      <div class="bar" style="height: 40%; background: #fb7185;"></div>
      <span class="day-lbl">Today</span>
    </div>
  </div>

  <div class="note-box" id="suggestionBox">
    💛 You've been carrying a lot these past few days. Remember you don't have to do it alone. Can your partner take the next feed?
  </div>

  <script>
    if (window.parent) {
      window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, '*');
    }
  </script>
</body>
</html>
"""

PARTNER_TASKS_CARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MA Partner Support Tasks</title>
  <style>
    :root {
      --bg: #121824;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.1);
      --accent: #10b981;
      --text: #f0f4f8;
      --text-muted: #94a3b8;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 16px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--card-border);
    }
    .title {
      font-size: 15px;
      font-weight: 600;
      color: var(--accent);
    }
    .task-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .task-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      margin-bottom: 6px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      font-size: 13px;
    }
    .task-item.completed {
      opacity: 0.5;
      text-decoration: line-through;
    }
    .task-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .checkbox {
      cursor: pointer;
      width: 16px;
      height: 16px;
      accent-color: var(--accent);
    }
    .tag {
      font-size: 10px;
      padding: 2px 6px;
      background: rgba(16, 185, 129, 0.15);
      border-radius: 4px;
      color: var(--accent);
    }
  </style>
</head>
<body>
  <div class="header">
    <span class="title">🤝 Partner Support Board</span>
    <span style="font-size: 12px; color: var(--text-muted);">Shared Effort</span>
  </div>

  <ul class="task-list" id="taskList">
    <li class="task-item">
      <div class="task-left">
        <input type="checkbox" class="checkbox" onclick="toggleTask(1, this)">
        <span>Sterilize and prep evening bottles</span>
      </div>
      <span class="tag">Partner</span>
    </li>
    <li class="task-item">
      <div class="task-left">
        <input type="checkbox" class="checkbox" onclick="toggleTask(2, this)">
        <span>Pick up size 2 diapers from store</span>
      </div>
      <span class="tag">Partner</span>
    </li>
    <li class="task-item">
      <div class="task-left">
        <input type="checkbox" class="checkbox" onclick="toggleTask(3, this)">
        <span>Take 4:00 AM baby shift so mom sleeps</span>
      </div>
      <span class="tag">Partner</span>
    </li>
  </ul>

  <script>
    function toggleTask(id, elem) {
      const item = elem.closest('.task-item');
      if (elem.checked) {
        item.classList.add('completed');
      } else {
        item.classList.remove('completed');
      }
      // Send tool call notification back to host
      if (window.parent) {
        window.parent.postMessage({
          jsonrpc: "2.0",
          method: "tools/call",
          params: { name: "partner_tasks", arguments: { action: "complete", task: String(id) } }
        }, '*');
      }
    }

    if (window.parent) {
      window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, '*');
    }
  </script>
</body>
</html>
"""

UI_RESOURCES = {
    "ui://ma/baby-summary-card": {
        "name": "Baby Summary Card",
        "description": "Visual timeline and summary of baby feeding and sleep rhythms",
        "mimeType": "text/html;profile=mcp-app",
        "html": BABY_SUMMARY_CARD_HTML,
    },
    "ui://ma/mood-trend-card": {
        "name": "Mother Mood Trend Card",
        "description": "Gentle visualization of mother's mood and rest over time",
        "mimeType": "text/html;profile=mcp-app",
        "html": MOOD_TREND_CARD_HTML,
    },
    "ui://ma/partner-tasks-card": {
        "name": "Partner Tasks Card",
        "description": "Interactive checklist of tasks assigned to partner for family teamwork",
        "mimeType": "text/html;profile=mcp-app",
        "html": PARTNER_TASKS_CARD_HTML,
    },
}
