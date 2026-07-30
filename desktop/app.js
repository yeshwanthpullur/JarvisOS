"use strict";

const token = document.querySelector('meta[name="jarvis-session"]').content;
const state = {
  activeRequestId: null,
  activeConversationId: null,
  currentView: "chat",
  lastAssistantText: "",
  autoScroll: true,
  eventSource: null,
};

const byId = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const request = { cache: "no-store", ...options };
  request.headers = { "Accept": "application/json", ...(options.headers || {}) };
  if (request.method === "POST") {
    request.headers["Content-Type"] = "application/json";
    request.headers["X-Jarvis-Session"] = token;
  }
  const response = await fetch(path, request);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function escapeLabel(value) {
  return String(value == null ? "None" : value);
}

function stateClass(value) {
  return String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "-");
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  byId("toast-region").append(toast);
  setTimeout(() => toast.remove(), 3500);
}

function setTheme(theme) {
  const resolved = theme === "system"
    ? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark")
    : theme;
  document.documentElement.dataset.theme = resolved;
}

function renderSafeContent(container, content) {
  container.replaceChildren();
  const parts = String(content).split("```");
  parts.forEach((part, index) => {
    if (index % 2 === 1) {
      const pre = document.createElement("pre");
      const code = document.createElement("code");
      code.textContent = part.replace(/^\w+\n/, "");
      pre.append(code);
      container.append(pre);
    } else if (part) {
      container.append(document.createTextNode(part));
    }
  });
}

function appendMessage(role, content, metadata = {}, status = "completed") {
  const welcome = document.querySelector(".welcome-state");
  if (welcome) welcome.remove();
  const article = document.createElement("article");
  article.className = `message ${role} ${status === "failed" ? "error" : ""}`;
  const head = document.createElement("div");
  head.className = "message-head";
  const author = document.createElement("strong");
  author.textContent = role === "user" ? "You" : "JARVIS";
  const timestamp = document.createElement("time");
  timestamp.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  head.append(author, timestamp);
  const body = document.createElement("div");
  body.className = "message-body";
  renderSafeContent(body, content);
  article.append(head, body);
  const values = [metadata.response_type, metadata.provider_id, metadata.model_id, metadata.command_name].filter(Boolean);
  if (values.length) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    values.forEach((value) => {
      const span = document.createElement("span");
      span.textContent = String(value);
      meta.append(span);
    });
    article.append(meta);
  }
  if (role === "assistant") {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    const copy = document.createElement("button");
    copy.type = "button";
    copy.textContent = "Copy";
    copy.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(String(content)); showToast("Response copied"); }
      catch { showToast("Copy is unavailable in this browser"); }
    });
    const speak = document.createElement("button");
    speak.type = "button";
    speak.textContent = "Speak";
    speak.addEventListener("click", () => speakText(String(content)));
    actions.append(copy, speak);
    article.append(actions);
    state.lastAssistantText = String(content);
  }
  byId("messages").append(article);
  if (state.autoScroll) article.scrollIntoView({ block: "end", behavior: "smooth" });
}

function setPending(active, label = "JARVIS is working") {
  byId("pending-strip").hidden = !active;
  byId("pending-label").textContent = label;
  byId("send-message").disabled = active;
  byId("cancel-request").disabled = !active;
  byId("message-input").disabled = active;
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text || state.activeRequestId) return;
  appendMessage("user", text);
  byId("message-input").value = "";
  setPending(true);
  try {
    const accepted = await api("/api/messages", {
      method: "POST",
      body: JSON.stringify({ message: text, conversation_id: state.activeConversationId }),
    });
    state.activeRequestId = accepted.interface_request_id;
    byId("stage-value").textContent = "Processing";
    const result = await waitForRequest(accepted.interface_request_id);
    appendMessage("assistant", result.content || result.errors?.join("\n") || "No response content.", result, result.status);
    updateExecutionMetadata(result);
    await Promise.all([loadConversations(), loadActivity(), loadApprovals(), loadStatus()]);
    if (result.command_name && result.command_name.startsWith("voice")) await loadVoice();
  } catch (error) {
    appendMessage("assistant", error.message, {}, "failed");
    showToast(error.message);
  } finally {
    state.activeRequestId = null;
    setPending(false);
    byId("message-input").disabled = false;
    byId("message-input").focus();
  }
}

async function waitForRequest(requestId) {
  const deadline = Date.now() + 125000;
  while (Date.now() < deadline) {
    const result = await api(`/api/requests/${encodeURIComponent(requestId)}`);
    if (!["accepted", "processing"].includes(result.status)) return result;
    await new Promise((resolve) => setTimeout(resolve, 350));
  }
  throw new Error("JARVIS did not finish within the interface timeout.");
}

function updateExecutionMetadata(result) {
  byId("stage-value").textContent = result.status || "Completed";
  byId("provider-value").textContent = result.provider_id || "None";
  byId("model-value").textContent = result.model_id || "None";
  byId("tool-value").textContent = result.tool_invocation_id || "None";
  byId("coordination-value").textContent = result.coordination_id || "None";
  byId("plan-value").textContent = result.plan_id || "None";
  byId("model-label").textContent = result.provider_id ? `${result.provider_id} / ${result.model_id || "default"}` : "No provider metadata";
}

async function cancelActive() {
  if (!state.activeRequestId) return;
  try {
    const result = await api("/api/cancel", { method: "POST", body: JSON.stringify({ request_id: state.activeRequestId }) });
    showToast(result.cancelled ? "Cancellation requested" : "The operation is no longer cancellable");
  } catch (error) { showToast(error.message); }
}

async function loadConversations() {
  const data = await api("/api/conversations");
  const list = byId("conversation-list");
  list.replaceChildren();
  if (!data.conversations.length) {
    list.innerHTML = '<p class="empty-copy">No conversations yet.</p>';
    return;
  }
  data.conversations.forEach((conversation) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `history-item ${conversation.active ? "active" : ""}`;
    const title = document.createElement("strong");
    title.textContent = conversation.title;
    const detail = document.createElement("span");
    detail.textContent = `${conversation.turns} turns`;
    button.append(title, detail);
    button.addEventListener("click", () => openConversation(conversation.conversation_id));
    list.append(button);
    if (conversation.active) state.activeConversationId = conversation.conversation_id;
  });
}

async function openConversation(conversationId) {
  const data = await api("/api/conversations/open", { method: "POST", body: JSON.stringify({ conversation_id: conversationId }) });
  state.activeConversationId = conversationId;
  const messages = byId("messages");
  messages.replaceChildren();
  (data.messages || []).forEach((message) => appendMessage(message.role, message.content, message.metadata || {}, message.status));
  await loadConversations();
  navigate("chat");
}

async function newConversation() {
  const data = await api("/api/conversations", { method: "POST", body: "{}" });
  state.activeConversationId = data.conversation_id;
  byId("messages").innerHTML = '<div class="welcome-state"><span class="welcome-mark" aria-hidden="true">J</span><h2>New conversation</h2><p>Chat normally or enter an existing JARVIS command.</p></div>';
  await loadConversations();
  navigate("chat");
}

function navigate(view) {
  state.currentView = view;
  document.querySelectorAll("[data-view-panel]").forEach((panel) => panel.classList.toggle("active", panel.dataset.viewPanel === view));
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  const labels = { chat: ["Conversation", "Local JARVIS session"], activity: ["Activity", "Observable execution"], plans: ["Plans", "Autonomous planning"], tools: ["Tools", "Governed capabilities"], multiagent: ["Multi-Agent", "Coordinated specialists"], voice: ["Voice", "Local speech controls"], health: ["Health", "Runtime readiness"], logs: ["Logs", "Safe observability"], settings: ["Settings", "Validated preferences"] };
  byId("view-title").textContent = labels[view][0];
  byId("view-subtitle").textContent = labels[view][1];
  document.body.classList.remove("nav-open");
  byId("sidebar").classList.remove("open");
  refreshView(view);
}

function renderRecords(targetId, records, descriptor) {
  const target = byId(targetId);
  target.replaceChildren();
  if (!records.length) {
    target.innerHTML = '<p class="empty-copy">Nothing to show.</p>';
    return;
  }
  records.forEach((item) => {
    const article = document.createElement("article");
    article.className = "record";
    const title = document.createElement("div");
    title.className = "record-title";
    const heading = document.createElement("h3");
    heading.textContent = descriptor.title(item);
    const status = document.createElement("span");
    const statusValue = descriptor.status(item);
    status.className = `state ${stateClass(statusValue)}`;
    status.textContent = escapeLabel(statusValue);
    title.append(heading, status);
    article.append(title);
    if (descriptor.summary) {
      const summary = document.createElement("p");
      summary.textContent = descriptor.summary(item);
      article.append(summary);
    }
    const grid = document.createElement("div");
    grid.className = "record-grid";
    descriptor.fields(item).forEach(([label, value]) => {
      const box = document.createElement("div");
      const span = document.createElement("span");
      span.textContent = label;
      const strong = document.createElement("strong");
      strong.textContent = escapeLabel(Array.isArray(value) ? value.join(", ") : value);
      box.append(span, strong);
      grid.append(box);
    });
    article.append(grid);
    target.append(article);
  });
}

async function loadActivity() {
  const data = await api("/api/activity");
  const records = [...data.activity].reverse();
  renderRecords("activity-list", records, {
    title: (item) => item.event_type.replaceAll("_", " "), status: (item) => item.status,
    summary: (item) => item.summary,
    fields: (item) => [["Request", item.request_id], ["Provider", item.provider_id], ["Model", item.model_id], ["Time", formatDate(item.created_at)]],
  });
  renderCompactActivity(records.slice(0, 6));
}

function renderCompactActivity(records) {
  const target = byId("activity-compact");
  target.replaceChildren();
  records.forEach((record) => {
    const item = document.createElement("div");
    item.className = "compact-event";
    item.textContent = record.summary;
    const detail = document.createElement("span");
    detail.textContent = `${record.status} | ${formatDate(record.created_at)}`;
    item.append(detail);
    target.append(item);
  });
}

async function loadPlans() {
  const data = await api("/api/plans");
  renderRecords("plans-list", data.plans, {
    title: (item) => item.title, status: (item) => item.status,
    summary: () => "Reviewable advisory plan; execution remains governed.",
    fields: (item) => [["Plan ID", item.plan_id], ["Version", item.version], ["Risk", item.risk], ["Steps", item.steps], ["Validated", item.validation]],
  });
}

async function loadTools() {
  const data = await api("/api/tools");
  renderRecords("tools-list", data.tools, {
    title: (item) => item.name, status: (item) => item.health,
    summary: (item) => item.description,
    fields: (item) => [["Tool ID", item.tool_id], ["Capabilities", item.capabilities], ["Operations", item.operations], ["Risk", item.risk_class], ["Dry run", item.dry_run]],
  });
}

async function loadMultiagent() {
  const data = await api("/api/multiagent");
  renderRecords("multiagent-list", data.coordinations, {
    title: (item) => item.objective, status: (item) => item.status,
    summary: (item) => `${item.mode} collaboration with ${item.agents.length} agents`,
    fields: (item) => [["Coordination", item.coordination_id], ["Agents", item.agents], ["Subtasks", item.subtasks.length], ["Conflicts", item.conflicts]],
  });
}

async function loadVoice() {
  const voice = await api("/api/voice");
  byId("voice-value").textContent = voice.output_enabled ? "Output enabled" : "Output disabled";
  const target = byId("voice-content");
  target.replaceChildren();
  const article = document.createElement("article");
  article.className = "record";
  const title = document.createElement("div");
  title.className = "record-title";
  const heading = document.createElement("h3");
  heading.textContent = "Local voice runtime";
  const stateBadge = document.createElement("span");
  stateBadge.className = `state ${stateClass(voice.tts_status)}`;
  stateBadge.textContent = escapeLabel(voice.tts_status);
  title.append(heading, stateBadge);
  article.append(title);
  const grid = document.createElement("div");
  grid.className = "record-grid";
  [["Output", voice.output_enabled ? "Enabled" : "Disabled"], ["TTS backend", voice.output_backend], ["STT backend", voice.input_backend], ["Microphone", voice.microphone_available ? "Available" : "Not configured"], ["STT", voice.stt_status], ["Privacy", voice.privacy_mode], ["Rate", voice.rate], ["Volume", voice.volume]].forEach(([label, value]) => {
    const box = document.createElement("div");
    const fieldLabel = document.createElement("span");
    fieldLabel.textContent = label;
    const fieldValue = document.createElement("strong");
    fieldValue.textContent = escapeLabel(value);
    box.append(fieldLabel, fieldValue);
    grid.append(box);
  });
  const actions = document.createElement("div");
  actions.className = "voice-actions";
  const toggle = document.createElement("button"); toggle.className = "button secondary"; toggle.type = "button"; toggle.textContent = voice.output_enabled ? "Disable output" : "Enable output"; toggle.addEventListener("click", () => updateSetting("voice", "output_enabled", !voice.output_enabled));
  const speak = document.createElement("button"); speak.className = "button primary"; speak.type = "button"; speak.textContent = "Speak last response"; speak.disabled = !voice.output_enabled || !state.lastAssistantText; speak.addEventListener("click", () => speakText(state.lastAssistantText));
  const stop = document.createElement("button"); stop.className = "button secondary"; stop.type = "button"; stop.textContent = "Stop speaking"; stop.addEventListener("click", stopVoice);
  actions.append(toggle, speak, stop);
  article.append(grid, actions);
  target.append(article);
}

async function speakText(text) {
  if (!text) return;
  try {
    const result = await api("/api/voice/speak", { method: "POST", body: JSON.stringify({ text }) });
    showToast(result.status === "completed" ? "Voice synthesis completed" : `Voice: ${result.status}`);
    await loadActivity();
  } catch (error) { showToast(error.message); }
}

async function stopVoice() {
  try { const result = await api("/api/voice/stop", { method: "POST", body: "{}" }); showToast(result.stopped ? "Voice stopped" : "No active speech output"); }
  catch (error) { showToast(error.message); }
}

async function loadHealth() {
  const health = await api("/api/health");
  const target = byId("health-grid");
  target.replaceChildren();
  Object.entries(health).forEach(([name, value]) => {
    const item = document.createElement("div");
    item.className = "health-item";
    const label = document.createElement("strong"); label.textContent = name.replaceAll("_", " ");
    const status = document.createElement("span"); status.className = `state ${stateClass(value)}`; status.textContent = escapeLabel(value);
    item.append(label, status); target.append(item);
  });
}

async function loadLogs() {
  const params = new URLSearchParams();
  const level = byId("log-level").value; const subsystem = byId("log-subsystem").value.trim(); const request = byId("log-request").value.trim();
  if (level) params.set("level", level); if (subsystem) params.set("subsystem", subsystem); if (request) params.set("request_id", request);
  const data = await api(`/api/logs?${params}`);
  const target = byId("logs-list"); target.replaceChildren();
  if (!data.logs.length) { target.innerHTML = '<p class="empty-copy">No matching safe log entries.</p>'; return; }
  data.logs.forEach((entry) => {
    const row = document.createElement("div"); row.className = "log-entry";
    [entry.timestamp, entry.level, entry.subsystem, entry.message].forEach((value, index) => { const span = document.createElement("span"); span.textContent = value; if (index === 1) span.className = entry.level; row.append(span); });
    target.append(row);
  });
}

async function loadApprovals() {
  const data = await api("/api/approvals");
  const target = byId("approval-list"); target.replaceChildren();
  if (!data.approvals.length) { target.innerHTML = '<p class="empty-copy">No pending approvals.</p>'; return; }
  data.approvals.forEach((approval) => {
    const article = document.createElement("article"); article.className = "record";
    const heading = document.createElement("h3"); heading.textContent = approval.action;
    const summary = document.createElement("p"); summary.textContent = `${approval.target}. ${approval.side_effects}`;
    const detail = document.createElement("p"); detail.textContent = `Risk: ${approval.risk_class} | Permission: ${approval.permission}`;
    const actions = document.createElement("div"); actions.className = "approval-actions";
    ["approve", "reject"].forEach((decision) => { const button = document.createElement("button"); button.type = "button"; button.className = `button ${decision === "approve" ? "primary" : "secondary"}`; button.textContent = decision === "approve" ? "Approve" : "Reject"; button.addEventListener("click", () => decideApproval(approval.approval_id, decision)); actions.append(button); });
    article.append(heading, summary, detail, actions); target.append(article);
  });
}

async function decideApproval(approvalId, decision) {
  if (decision === "approve" && !confirm("Approve this specific governed plan? This does not execute it.")) return;
  try { const result = await api("/api/approvals/decision", { method: "POST", body: JSON.stringify({ approval_id: approvalId, decision }) }); showToast(result.content); await Promise.all([loadApprovals(), loadPlans()]); }
  catch (error) { showToast(error.message); }
}

async function loadSettings() {
  const data = await api("/api/settings");
  state.autoScroll = data.interface.auto_scroll;
  setTheme(data.interface.theme);
  document.body.classList.toggle("compact", data.interface.density === "compact");
  const target = byId("settings-content"); target.replaceChildren();
  target.append(
    settingsSection("Interface", [
      selectSetting("Theme", "interface", "theme", data.interface.theme, ["system", "dark", "light"]),
      selectSetting("Density", "interface", "density", data.interface.density, ["comfortable", "compact"]),
      toggleSetting("Auto-scroll", "interface", "auto_scroll", data.interface.auto_scroll),
      toggleSetting("Notifications", "interface", "notifications", data.interface.notifications),
      readOnlySetting("Local port", data.interface.port),
    ]),
    settingsSection("Provider", [
      selectSetting("Execution policy", "provider", "execution_policy", data.provider.execution_policy, ["automatic", "local_only", "cloud_only", "prefer_local", "prefer_cloud"]),
      textSetting("Provider preference", "provider", "provider_preference", data.provider.provider_preference || ""),
      textSetting("Model preference", "provider", "model_preference", data.provider.model_preference || ""),
    ]),
    settingsSection("Voice", [
      toggleSetting("Output enabled", "voice", "output_enabled", data.voice.output_enabled),
      selectSetting("Privacy", "voice", "privacy_mode", data.voice.privacy_mode, ["strict", "standard", "diagnostic"]),
      selectSetting("Language", "voice", "language", data.voice.language, ["en-US", "en-GB"]),
      numberSetting("Rate", "voice", "rate", data.voice.rate, -10, 10),
      numberSetting("Volume", "voice", "volume", data.voice.volume, 0, 100),
      toggleSetting("Keep raw audio", "voice", "raw_audio_persistence", data.voice.raw_audio_persistence),
      readOnlySetting("TTS backend", data.voice.output_backend),
      readOnlySetting("STT", data.voice.stt_status),
    ]),
    settingsSection("Governance", [
      selectSetting("Tool mode", "tool", "mode", data.tool.mode, ["off", "confirm", "automatic-safe", "automatic"]),
      selectSetting("Multi-Agent mode", "multiagent", "mode", data.multiagent.mode, ["off", "confirm", "automatic-safe", "automatic"]),
      selectSetting("Planning mode", "planning", "mode", data.planning.mode, ["off", "suggest", "confirm", "automatic-safe"]),
    ]),
    shutdownSetting(),
  );
}

function settingsSection(title, fields) {
  const section = document.createElement("section"); section.className = "settings-section";
  const heading = document.createElement("h3"); heading.textContent = title;
  const grid = document.createElement("div"); grid.className = "settings-grid"; fields.forEach((field) => grid.append(field));
  section.append(heading, grid); return section;
}

function selectSetting(label, section, key, current, values) {
  const wrapper = document.createElement("div"); wrapper.className = "setting-field";
  const fieldLabel = document.createElement("label"); fieldLabel.textContent = label;
  const select = document.createElement("select"); values.forEach((value) => { const option = document.createElement("option"); option.value = value; option.textContent = value.replaceAll("_", " "); option.selected = value === current; select.append(option); });
  select.addEventListener("change", () => updateSetting(section, key, select.value)); fieldLabel.append(select); wrapper.append(fieldLabel); return wrapper;
}

function toggleSetting(label, section, key, current) {
  const wrapper = document.createElement("div"); wrapper.className = "setting-field";
  const button = document.createElement("button"); button.type = "button"; button.className = "button secondary"; button.textContent = `${label}: ${current ? "On" : "Off"}`; button.addEventListener("click", () => updateSetting(section, key, !current)); wrapper.append(button); return wrapper;
}

function readOnlySetting(label, value) {
  const wrapper = document.createElement("div"); wrapper.className = "setting-field";
  const fieldLabel = document.createElement("label"); fieldLabel.textContent = label;
  const input = document.createElement("input"); input.value = escapeLabel(value); input.readOnly = true; fieldLabel.append(input); wrapper.append(fieldLabel); return wrapper;
}

function textSetting(label, section, key, current) {
  const wrapper = document.createElement("div"); wrapper.className = "setting-field";
  const fieldLabel = document.createElement("label"); fieldLabel.textContent = label;
  const row = document.createElement("div"); row.className = "setting-input-row";
  const input = document.createElement("input"); input.value = current; input.maxLength = 120; input.placeholder = "Automatic";
  const apply = document.createElement("button"); apply.type = "button"; apply.className = "button secondary"; apply.textContent = "Apply";
  apply.addEventListener("click", () => updateSetting(section, key, input.value.trim()));
  row.append(input, apply); fieldLabel.append(row); wrapper.append(fieldLabel); return wrapper;
}

function numberSetting(label, section, key, current, minimum, maximum) {
  const wrapper = document.createElement("div"); wrapper.className = "setting-field";
  const fieldLabel = document.createElement("label"); fieldLabel.textContent = label;
  const input = document.createElement("input"); input.type = "number"; input.min = String(minimum); input.max = String(maximum); input.value = String(current);
  input.addEventListener("change", () => updateSetting(section, key, Number(input.value)));
  fieldLabel.append(input); wrapper.append(fieldLabel); return wrapper;
}

function shutdownSetting() {
  const section = document.createElement("section"); section.className = "settings-section danger-section";
  const heading = document.createElement("h3"); heading.textContent = "Application";
  const copy = document.createElement("p"); copy.textContent = "Stop the local interface and release its port cleanly.";
  const button = document.createElement("button"); button.type = "button"; button.className = "button danger"; button.textContent = "Shut down JARVIS";
  button.addEventListener("click", shutdownJarvis); section.append(heading, copy, button); return section;
}

async function shutdownJarvis() {
  if (!confirm("Shut down this local JARVIS interface?")) return;
  try {
    await api("/api/shutdown", { method: "POST", body: "{}" });
    document.body.classList.add("offline");
    showToast("JARVIS is shutting down");
  } catch (error) { showToast(error.message); }
}

async function updateSetting(section, key, value) {
  try { await api("/api/settings", { method: "POST", body: JSON.stringify({ section, key, value }) }); showToast("Setting updated"); await loadSettings(); if (section === "voice") await loadVoice(); await loadStatus(); }
  catch (error) { showToast(error.message); }
}

async function loadStatus() {
  const status = await api("/api/status");
  state.activeConversationId = status.conversation_id;
  byId("runtime-label").textContent = status.runtime;
  byId("runtime-dot").className = `status-dot ${status.runtime === "running" ? "healthy" : "unavailable"}`;
  byId("policy-badge").textContent = status.local_only ? "local only" : status.cloud_only ? "cloud only" : status.execution_policy;
  const provider = status.last_provider || status.provider_preference;
  const model = status.last_model || status.model_preference;
  byId("model-label").textContent = provider ? `${provider} / ${model || "default"}` : "Provider automatic";
  byId("provider-value").textContent = provider || "None";
  byId("model-value").textContent = model || "None";
}

function formatDate(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? String(value) : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

async function refreshView(view) {
  const loaders = { activity: loadActivity, plans: loadPlans, tools: loadTools, multiagent: loadMultiagent, voice: loadVoice, health: loadHealth, logs: loadLogs, settings: loadSettings };
  if (loaders[view]) {
    try { await loaders[view](); } catch (error) { showToast(error.message); }
  }
}

function connectEvents() {
  if (!window.EventSource) return;
  state.eventSource = new EventSource("/api/events");
  state.eventSource.addEventListener("activity", (event) => {
    const record = JSON.parse(event.data);
    byId("stage-value").textContent = record.summary;
    if (record.provider_id) byId("provider-value").textContent = record.provider_id;
    if (record.model_id) byId("model-value").textContent = record.model_id;
    loadActivity().catch(() => {});
  });
  state.eventSource.onerror = () => {
    state.eventSource.close();
    state.eventSource = null;
    setTimeout(() => loadActivity().catch(() => {}), 1000);
  };
}

function bindEvents() {
  byId("composer").addEventListener("submit", (event) => { event.preventDefault(); sendMessage(byId("message-input").value); });
  byId("message-input").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); byId("composer").requestSubmit(); } });
  byId("cancel-request").addEventListener("click", cancelActive);
  byId("new-conversation").addEventListener("click", newConversation);
  byId("refresh-history").addEventListener("click", loadConversations);
  byId("refresh-approvals").addEventListener("click", loadApprovals);
  byId("theme-toggle").addEventListener("click", () => updateSetting("interface", "theme", document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
  byId("sidebar-toggle").addEventListener("click", () => byId("sidebar").classList.toggle("open"));
  byId("activity-toggle").addEventListener("click", () => byId("activity-panel").classList.toggle("open"));
  byId("close-activity").addEventListener("click", () => byId("activity-panel").classList.remove("open"));
  byId("log-filters").addEventListener("submit", (event) => { event.preventDefault(); loadLogs(); });
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.view)));
  document.querySelectorAll("[data-refresh]").forEach((button) => button.addEventListener("click", () => refreshView(button.dataset.refresh)));
  document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));
}

async function initialize() {
  bindEvents();
  try {
    const bootstrap = await api("/api/bootstrap");
    setTheme(bootstrap.settings.interface.theme);
    document.body.classList.toggle("compact", bootstrap.settings.interface.density === "compact");
    state.autoScroll = bootstrap.settings.interface.auto_scroll;
    state.activeConversationId = bootstrap.status.conversation_id;
    await Promise.all([loadStatus(), loadConversations(), loadActivity(), loadApprovals(), loadVoice()]);
    connectEvents();
  } catch (error) {
    byId("runtime-label").textContent = "Unavailable";
    byId("runtime-dot").className = "status-dot unavailable";
    showToast(`Interface startup failed: ${error.message}`);
  }
}

window.addEventListener("beforeunload", () => state.eventSource?.close());
initialize();
