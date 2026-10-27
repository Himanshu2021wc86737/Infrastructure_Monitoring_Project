async function getJSON(url, options={}) {
  const r = await fetch(url, options);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}
function esc(v){return String(v ?? "").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
async function loadSummary(){
  const s=await getJSON("/api/summary");
  for(const k of ["total","healthy","warning","critical"]) document.getElementById(k).textContent=s[k.toUpperCase?.() || k] ?? s[k];
  document.getElementById("total").textContent=s.total;
  document.getElementById("healthy").textContent=s.HEALTHY;
  document.getElementById("warning").textContent=s.WARNING;
  document.getElementById("critical").textContent=s.CRITICAL;
}
async function loadServers(){
  const rows=await getJSON("/api/servers");
  const body=document.getElementById("servers");
  body.innerHTML=rows.map(x=>`<tr>
    <td><b>${esc(x.name)}</b></td><td>${esc(x.host)}</td><td>${esc(x.environment)}</td>
    <td>${x.cpu}%</td><td>${x.memory}%</td><td>${x.disk}%</td>
    <td>${x.health_score}/100</td><td class="status ${x.status}">${x.status}</td>
  </tr>`).join("") || '<tr><td colspan="8">No servers yet. Click "Collect Local Metrics".</td></tr>';
}
async function loadAlerts(){
  const rows=await getJSON("/api/alerts");
  document.getElementById("alerts").innerHTML=rows.map(x=>`<div class="alert ${x.severity}">
    <b>${esc(x.severity)} — ${esc(x.server_name||"Unknown")}</b><br>${esc(x.message)}<br><small>${esc(x.timestamp)}</small>
  </div>`).join("") || "<p>No alerts.</p>";
}
async function loadAll(){try{await Promise.all([loadSummary(),loadServers(),loadAlerts()])}catch(e){alert(e.message)}}
async function collectLocal(){
  try{await getJSON("/api/collect",{method:"POST"}); await loadAll();}catch(e){alert(e.message)}
}
loadAll();

async function autoUpdate() {
  try {
    await getJSON("/api/collect", { method: "POST" });
    await loadAll();
  } catch (e) {
    console.error("Auto-update failed:", e);
  }
}

setInterval(autoUpdate, 30000);
