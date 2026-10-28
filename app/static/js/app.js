
async function getJSON(url, options = {}) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[m]);
}

function num(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function progressBar(value, label) {
  const n = Math.max(0, Math.min(100, num(value)));
  const color = n >= 90 ? "metric-red"
    : n >= 80 ? "metric-amber" : "metric-green";

  return `<div class="metric-cell">
    <div class="metric-line">${num(value).toFixed(1)}%</div>
    <div class="metric-track" role="progressbar"
      aria-label="${label}" aria-valuemin="0"
      aria-valuemax="100" aria-valuenow="${n}">
      <span class="metric-fill ${color}" style="width:${n}%"></span>
    </div>
  </div>`;
}

function statusBadge(status) {
  const s = String(status || "UNKNOWN").toUpperCase();
  const c = ["HEALTHY", "ONLINE", "UP"].includes(s)
    ? "status-healthy"
    : ["WARNING", "WARN"].includes(s)
      ? "status-warning"
      : ["CRITICAL", "DOWN", "OFFLINE"].includes(s)
        ? "status-critical"
        : "status-unknown";

  return `<span class="status-badge ${c}">
    <span class="badge-dot"></span>${esc(s)}
  </span>`;
}

function healthScore(value) {
  const n = Math.max(0, Math.min(100, num(value)));
  const c = n < 60 ? "score-critical"
    : n < 80 ? "score-warning" : "score-good";

  return `<span class="score-value ${c}">${n.toFixed(1)}<small>/100</small></span>`;
}

async function loadSummary() {
  const s = await getJSON("/api/summary");

  document.getElementById("total").textContent =
    s.total ?? s.TOTAL ?? 0;
  document.getElementById("healthy").textContent =
    s.HEALTHY ?? s.healthy ?? 0;
  document.getElementById("warning").textContent =
    s.WARNING ?? s.warning ?? 0;
  document.getElementById("critical").textContent =
    s.CRITICAL ?? s.critical ?? 0;
}

async function loadServers() {
  const rows = await getJSON("/api/servers");
  const body = document.getElementById("servers");

  if (!Array.isArray(rows) || rows.length === 0) {
    body.innerHTML =
      '<tr><td colspan="8" class="loading-cell">No servers found.</td></tr>';
    return;
  }

  body.innerHTML = rows.map(x => `<tr>
    <td>
      <div class="server-name">
        <span class="server-icon">▤</span>
        <b>${esc(x.name)}</b>
      </div>
    </td>
    <td>${esc(x.host)}</td>
    <td><span class="environment-tag">${esc(x.environment || "N/A")}</span></td>
    <td>${progressBar(x.cpu, "CPU usage")}</td>
    <td>${progressBar(x.memory, "Memory usage")}</td>
    <td>${progressBar(x.disk, "Disk usage")}</td>
    <td>${healthScore(x.health_score)}</td>
    <td>${statusBadge(x.status)}</td>
  </tr>`).join("");
}

async function loadAlerts() {
  const rows = await getJSON("/api/alerts");
  const box = document.getElementById("alerts");

  if (!Array.isArray(rows) || rows.length === 0) {
    box.innerHTML = '<p class="empty-state">No recent alerts.</p>';
    return;
  }

  box.innerHTML = rows.map(x => {
    const s = String(x.severity || "INFO").toUpperCase();
    const c = s === "CRITICAL" ? "alert-critical"
      : ["WARNING", "WARN"].includes(s)
        ? "alert-warning" : "alert-info";

    const symbol = s === "CRITICAL" ? "!" :
      ["WARNING", "WARN"].includes(s) ? "⚠" : "i";

    return `<div class="alert-item ${c}">
      <span class="alert-symbol">${symbol}</span>
      <div class="alert-content">
        <div class="alert-title">
          <b>${esc(s)}</b>
          <span>${esc(x.server_name || "Unknown")}</span>
        </div>
        <p>${esc(x.message)}</p>
        <small>${esc(x.timestamp)}</small>
      </div>
    </div>`;
  }).join("");
}

/* METRICS HISTORY CHART */

let historyRequest = 0;

function createHistoryPanel() {
  let panel = document.getElementById("history-panel");
  if (panel) return panel;

  panel = document.createElement("section");
  panel.id = "history-panel";
  panel.className = "panel";
  panel.style.marginBottom = "24px";

  panel.innerHTML = `
    <div style="padding:20px">
      <h2 style="margin:0 0 8px">Metrics History</h2>
      <p style="margin:0 0 16px;color:#8792a5">
        CPU, Memory and Disk usage over the latest readings
      </p>

      <label for="history-server">Select server: </label>
      <select id="history-server"
        style="padding:9px;margin:8px 0 16px;max-width:100%">
      </select>

      <div style="width:100%;height:280px;position:relative">
        <canvas id="history-chart"
          role="img"
          aria-label="CPU, memory and disk usage history"
          style="width:100%;height:280px;display:block">
        </canvas>
      </div>

      <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:13px">
        <span style="color:#3b82f6">● CPU</span>
        <span style="color:#10b981">● Memory</span>
        <span style="color:#f59e0b">● Disk</span>
      </div>

      <p id="history-message" role="status"
        style="color:#8792a5;margin-top:12px">
        Loading metrics history...
      </p>
    </div>
  `;

  const target = document.getElementById("server-inventory");
  if (target && target.parentNode) {
    target.parentNode.insertBefore(panel, target);
  } else {
    document.querySelector(".main-content")?.appendChild(panel);
  }

  document.getElementById("history-server")
    .addEventListener("change", event => {
      drawHistoryChart(event.target.value);
    });

  return panel;
}

async function loadHistoryChart() {
  try {
    const servers = await getJSON("/api/servers");
    if (!Array.isArray(servers)) return;

    createHistoryPanel();

    const select = document.getElementById("history-server");
    const previous = select.value;

    select.innerHTML = servers.map(s =>
      `<option value="${Number(s.id)}">${esc(s.name)}</option>`
    ).join("");

    if (servers.length === 0) {
      document.getElementById("history-message").textContent =
        "No servers available.";
      return;
    }

    if (servers.some(s => String(s.id) === previous)) {
      select.value = previous;
    }

    await drawHistoryChart(select.value);
  } catch (e) {
    console.error("History chart loading failed:", e);
    const message = document.getElementById("history-message");
    if (message) {
      message.textContent = "Unable to load server history.";
    }
  }
}

async function drawHistoryChart(serverId) {
  if (!serverId) return;

  const requestId = ++historyRequest;
  const message = document.getElementById("history-message");
  const canvas = document.getElementById("history-chart");

  if (!canvas || !message) return;

  message.textContent = "Loading history...";

  try {
    const rows = await getJSON(
      `/api/server/${Number(serverId)}/history`
    );

    // Ignore an older request if the user selected another server
    if (requestId !== historyRequest) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = 280;

    if (!width) {
      message.textContent = "Chart is waiting for the page layout.";
      return;
    }

    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    if (!Array.isArray(rows) || rows.length === 0) {
      message.textContent =
        "No history yet. Wait for metric readings or run the simulator.";
      return;
    }

    message.textContent =
      `Showing ${rows.length} saved readings.`;

    const left = 40;
    const right = 12;
    const top = 18;
    const bottom = 28;
    const plotWidth = Math.max(1, width - left - right);
    const plotHeight = height - top - bottom;

    ctx.font = "11px Arial";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.strokeStyle = "#dfe5ed";
    ctx.fillStyle = "#8792a5";
    ctx.lineWidth = 1;

    for (let value = 0; value <= 100; value += 20) {
      const y = top + plotHeight * (1 - value / 100);

      ctx.beginPath();
      ctx.moveTo(left, y);
      ctx.lineTo(width - right, y);
      ctx.stroke();

      ctx.fillText(String(value), left - 8, y);
    }

    const series = [
      { key: "cpu", color: "#3b82f6" },
      { key: "memory", color: "#10b981" },
      { key: "disk", color: "#f59e0b" }
    ];

    series.forEach(line => {
      ctx.beginPath();
      ctx.strokeStyle = line.color;
      ctx.lineWidth = 2.5;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";

      rows.forEach((row, index) => {
        const x = rows.length === 1
          ? left + plotWidth / 2
          : left + (index / (rows.length - 1)) * plotWidth;

        const value = Math.max(
          0, Math.min(100, num(row[line.key]))
        );
        const y = top + plotHeight * (1 - value / 100);

        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      ctx.stroke();
    });

    // Show first and last reading positions
    ctx.fillStyle = "#8792a5";
    ctx.font = "10px Arial";
    ctx.textAlign = "left";
    ctx.fillText("Oldest", left, height - 8);
    ctx.textAlign = "right";
    ctx.fillText("Latest", width - right, height - 8);
  } catch (e) {
    if (requestId !== historyRequest) return;

    console.error("Could not draw metrics history:", e);
    message.textContent =
      "Could not load history. Please check the server and try again.";
  }
}

/* DASHBOARD REFRESH */

let loading = false;

async function loadAll() {
  if (loading) return;
  loading = true;

  try {
    await Promise.all([
      loadSummary(),
      loadServers(),
      loadAlerts()
    ]);

    await loadHistoryChart();
  } catch (e) {
    console.error("Dashboard update failed:", e);
  } finally {
    loading = false;
  }
}

async function collectLocal() {
  const button = document.querySelector(
    'button[onclick="collectLocal()"]'
  );

  try {
    if (button) button.disabled = true;

    await getJSON("/api/collect", { method: "POST" });
    await loadAll();
  } catch (e) {
    console.error("Metric collection failed:", e);
    alert("Metric collection failed. Check the server and try again.");
  } finally {
    if (button) button.disabled = false;
  }
}

loadAll();
setInterval(loadAll, 30000);
