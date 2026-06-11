const statusEl = document.querySelector("#status");
const statusText = document.querySelector("#statusText");
const modelEl = document.querySelector("#model");
const deviceEl = document.querySelector("#device");
const epEl = document.querySelector("#ep");
const endpointEl = document.querySelector("#endpoint");
const promptEl = document.querySelector("#prompt");
const runButton = document.querySelector("#runButton");
const eventsEl = document.querySelector("#events");
const answerEl = document.querySelector("#answer");
const toolCountEl = document.querySelector("#toolCount");
const latencyEl = document.querySelector("#latency");
const totalMsEl = document.querySelector("#totalMs");
const finalMsEl = document.querySelector("#finalMs");
const tpsEl = document.querySelector("#tps");

function setText(el, value) {
  el.textContent = value ?? "-";
}

function formatMs(value) {
  if (!Number.isFinite(value)) return "-";
  return value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${value}ms`;
}

function renderJson(value) {
  return JSON.stringify(value, null, 2);
}

async function refreshStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    statusEl.classList.toggle("ready", data.ok);
    setText(statusText, data.ok ? "NPU ready" : "Offline");
    setText(modelEl, data.model);
    setText(deviceEl, data.device);
    setText(epEl, data.execution_provider);
    setText(endpointEl, data.endpoint);
  } catch (error) {
    statusEl.classList.remove("ready");
    setText(statusText, "Offline");
    setText(modelEl, "-");
    setText(deviceEl, "-");
    setText(epEl, "-");
    setText(endpointEl, "-");
  }
}

function renderEvents(events) {
  toolCountEl.textContent = String(events.length);
  if (!events.length) {
    eventsEl.className = "events empty";
    eventsEl.textContent = "No tool calls returned.";
    return;
  }
  eventsEl.className = "events";
  eventsEl.innerHTML = events
    .map(
      (event) => `
        <div class="event">
          <div class="event-title">
            <span>${event.name}</span>
            <small>${formatMs(event.elapsed_ms)}</small>
          </div>
          <pre>${renderJson({ source: event.source, arguments: event.arguments, result: event.result })}</pre>
        </div>
      `
    )
    .join("");
}

async function runAgent() {
  const prompt = promptEl.value.trim();
  if (!prompt) return;
  runButton.disabled = true;
  runButton.textContent = "Running";
  answerEl.className = "answer empty";
  answerEl.textContent = "Calling the local NPU model...";
  eventsEl.className = "events empty";
  eventsEl.textContent = "Waiting for tool calls...";
  latencyEl.textContent = "-";
  totalMsEl.textContent = "-";
  finalMsEl.textContent = "-";
  tpsEl.textContent = "-";

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 52000);
    const res = await fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Agent request failed");

    renderEvents(data.events || []);
    answerEl.className = "answer";
    answerEl.textContent = data.answer || "(empty response)";
    setText(latencyEl, formatMs(data.metrics?.total_ms));
    setText(totalMsEl, formatMs(data.metrics?.total_ms));
    setText(finalMsEl, formatMs(data.metrics?.final_call_ms));
    setText(tpsEl, data.metrics?.tokens_per_second ? String(data.metrics.tokens_per_second) : "-");
    setText(modelEl, data.model);
    setText(endpointEl, data.endpoint);
  } catch (error) {
    answerEl.className = "answer";
    answerEl.textContent = error.name === "AbortError" ? "The agent run timed out. Restart the local bridge and try again." : error.message;
    eventsEl.className = "events empty";
    eventsEl.textContent = "The agent request failed.";
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run Agent";
    refreshStatus();
  }
}

runButton.addEventListener("click", runAgent);
refreshStatus();
setInterval(refreshStatus, 8000);
