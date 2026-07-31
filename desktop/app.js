"use strict";

const token = document.querySelector('meta[name="jarvis-session"]').content;
const state = {
  activeRequestId: null,
  activeConversationId: null,
  currentView: "chat",
  lastAssistantText: "",
  lastUserText: "",
  autoScroll: true,
  eventSource: null,
  eventTimer: null,
  reconnectAttempt: 0,
  lastEventSequence: 0,
  seenEvents: new Set(),
  connected: false,
  speaking: false,
  requestStartedAt: 0,
  requestTimer: null,
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
  let payload;
  try { payload = await response.json(); }
  catch { throw new Error(`JARVIS returned an unreadable response (${response.status}).`); }
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

function setConnection(mode, message = "") {
  state.connected = mode === "online";
  document.body.classList.toggle("offline", mode === "offline");
  const banner = byId("connection-banner");
  banner.hidden = mode === "online";
  byId("connection-message").textContent = message || (mode === "reconnecting" ? "Reconnecting to JARVIS..." : "JARVIS is offline. Your draft is safe.");
  if (mode === "reconnecting") setAssistantState("starting", "Reconnecting");
  if (mode === "offline") setAssistantState("offline", "Connection unavailable");
  if (mode === "online" && !state.activeRequestId && !state.speaking) setAssistantState("idle", "System ready");
}

function setAssistantState(mode, label) {
  const allowed = new Set(["starting", "idle", "thinking", "listening", "speaking", "error", "offline"]);
  const resolved = allowed.has(mode) ? mode : "idle";
  document.body.dataset.assistantState = resolved;
  const labels = { starting: "Initializing", idle: "System ready", thinking: "Reasoning", listening: "Listening", speaking: "Speaking", error: "Attention required", offline: "Disconnected" };
  const value = label || labels[resolved];
  const presence = byId("presence-state");
  if (presence) presence.textContent = value;
  byId("identity-state").textContent = value;
  byId("composer-state").textContent = value;
  byId("composer-dot").className = `status-dot ${resolved === "idle" ? "healthy" : resolved === "thinking" || resolved === "speaking" ? "processing" : resolved === "error" || resolved === "offline" ? "failed" : ""}`;
}

function setTheme(theme) {
  const resolved = theme === "system"
    ? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark")
    : theme;
  document.documentElement.dataset.theme = resolved;
}

function appendInlineMarkdown(target, text) {
  const tokens = String(text).split(/(`[^`\n]+`|\*\*[^*\n]+\*\*|\[[^\]\n]+\]\(https?:\/\/[^)\s]+\))/g);
  tokens.forEach((token) => {
    if (/^`[^`]+`$/.test(token)) {
      const code = document.createElement("code"); code.textContent = token.slice(1, -1); target.append(code);
    } else if (/^\*\*[^*]+\*\*$/.test(token)) {
      const strong = document.createElement("strong"); strong.textContent = token.slice(2, -2); target.append(strong);
    } else {
      const link = token.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/);
      if (link) { const anchor = document.createElement("a"); anchor.textContent = link[1]; anchor.href = link[2]; anchor.target = "_blank"; anchor.rel = "noopener noreferrer"; target.append(anchor); }
      else target.append(document.createTextNode(token));
    }
  });
}

function renderSafeContent(container, content) {
  container.replaceChildren();
  const source = String(content || "").replace(/\r\n/g, "\n");
  const chunks = source.split(/```/);
  chunks.forEach((chunk, chunkIndex) => {
    if (chunkIndex % 2 === 1) {
      const firstBreak = chunk.indexOf("\n");
      const language = firstBreak >= 0 ? chunk.slice(0, firstBreak).trim().replace(/[^a-z0-9_+-]/gi, "").slice(0, 18) : "code";
      const codeText = firstBreak >= 0 ? chunk.slice(firstBreak + 1) : chunk;
      const pre = document.createElement("pre"); pre.dataset.language = language || "code";
      const code = document.createElement("code"); code.textContent = codeText.trimEnd(); pre.append(code); container.append(pre);
      return;
    }
    const lines = chunk.split("\n");
    let list = null;
    lines.forEach((line) => {
      if (!line.trim()) { list = null; return; }
      const heading = line.match(/^(#{1,3})\s+(.+)$/);
      const bullet = line.match(/^\s*[-*]\s+(.+)$/);
      const numbered = line.match(/^\s*\d+\.\s+(.+)$/);
      if (heading) { list = null; const node = document.createElement(`h${Math.min(3, heading[1].length)}`); appendInlineMarkdown(node, heading[2]); container.append(node); }
      else if (bullet || numbered) {
        const kind = bullet ? "ul" : "ol";
        if (!list || list.tagName.toLowerCase() !== kind) { list = document.createElement(kind); container.append(list); }
        const item = document.createElement("li"); appendInlineMarkdown(item, (bullet || numbered)[1]); list.append(item);
      } else { list = null; const paragraph = document.createElement("p"); appendInlineMarkdown(paragraph, line); container.append(paragraph); }
    });
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
  const labels = { user: "You", assistant: "JARVIS", system: "System", tool: "Tool Intelligence", planning: "Planning" };
  author.textContent = labels[role] || "JARVIS";
  const timestamp = document.createElement("time");
  timestamp.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  head.append(author, timestamp);
  const body = document.createElement("div");
  body.className = "message-body";
  renderSafeContent(body, content);
  article.append(head, body);
  const values = [metadata.response_type, metadata.provider_id, metadata.model_id, metadata.command_name].filter(Boolean);
  if (values.length) {
    const meta = document.createElement("details"); meta.className = "message-meta";
    const summary = document.createElement("summary"); summary.className = "meta-toggle"; summary.textContent = "Execution details";
    const detail = document.createElement("div"); detail.className = "meta-detail";
    values.forEach((value) => {
      const span = document.createElement("span");
      span.textContent = String(value);
      detail.append(span);
    });
    meta.append(summary, detail); article.append(meta);
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
    const retry = document.createElement("button"); retry.type = "button"; retry.textContent = "Retry"; retry.disabled = !state.lastUserText; retry.addEventListener("click", () => sendMessage(state.lastUserText));
    actions.append(copy, speak, retry);
    article.append(actions);
    state.lastAssistantText = String(content);
  }
  byId("messages").append(article);
  if (state.autoScroll) article.scrollIntoView({ block: "end", behavior: "smooth" });
  else byId("scroll-latest").hidden = false;
}

function restoreWelcome(title = "How can I assist?", copy = "One channel for conversation, governed tools, plans, and local intelligence.") {
  const messages = byId("messages"); messages.replaceChildren();
  const welcome = document.createElement("div"); welcome.className = "welcome-state";
  const visualizer = document.createElement("div"); visualizer.className = "assistant-visualizer"; visualizer.id = "assistant-visualizer"; visualizer.setAttribute("aria-hidden", "true");
  ["orbit orbit-outer", "orbit orbit-mid", "orbit orbit-inner"].forEach((className) => { const node = document.createElement("span"); node.className = className; visualizer.append(node); });
  const core = document.createElement("span"); core.className = "core-light";
  const waveform = document.createElement("span"); waveform.className = "waveform"; for (let index = 0; index < 7; index += 1) waveform.append(document.createElement("i"));
  visualizer.append(core, waveform);
  const presence = document.createElement("div"); presence.className = "presence-label";
  const left = document.createElement("span"); left.className = "presence-line";
  const stateLabel = document.createElement("span"); stateLabel.id = "presence-state"; stateLabel.textContent = "System ready";
  const right = document.createElement("span"); right.className = "presence-line"; presence.append(left, stateLabel, right);
  const heading = document.createElement("h2"); heading.textContent = title;
  const paragraph = document.createElement("p"); paragraph.textContent = copy;
  const actions = document.createElement("div"); actions.className = "quick-actions"; actions.setAttribute("aria-label", "Suggested actions");
  [["System brief", "What is the current system status?"], ["Resume context", "What were we doing?"], ["Voice status", "voice status"]].forEach(([label, prompt]) => { const button = document.createElement("button"); button.type = "button"; button.textContent = label; button.dataset.prompt = prompt; button.addEventListener("click", () => sendMessage(prompt)); actions.append(button); });
  welcome.append(visualizer, presence, heading, paragraph, actions); messages.append(welcome);
}

function resizeComposer() {
  const input = byId("message-input"); input.style.height = "auto"; input.style.height = `${Math.min(150, Math.max(42, input.scrollHeight))}px`;
}

function setPending(active, label = "JARVIS is working") {
  byId("pending-strip").hidden = !active;
  byId("pending-label").textContent = label;
  byId("send-message").disabled = active;
  byId("cancel-request").hidden = !active;
  byId("cancel-request").disabled = !active;
  byId("message-input").readOnly = active;
  if (state.requestTimer) clearInterval(state.requestTimer);
  if (active) {
    state.requestStartedAt = Date.now();
    state.requestTimer = setInterval(() => { const seconds = Math.floor((Date.now() - state.requestStartedAt) / 1000); byId("processing-time").textContent = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`; }, 1000);
    setAssistantState("thinking", label);
  } else {
    state.requestTimer = null; byId("processing-time").textContent = "00:00";
    if (state.connected && !state.speaking) setAssistantState("idle", "System ready");
  }
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text || state.activeRequestId) return;
  state.lastUserText = text;
  appendMessage("user", text);
  setPending(true);
  let accepted = false;
  try {
    const response = await api("/api/messages", {
      method: "POST",
      body: JSON.stringify({ message: text, conversation_id: state.activeConversationId }),
    });
    accepted = true;
    byId("message-input").value = "";
    resizeComposer();
    state.activeRequestId = response.interface_request_id;
    byId("stage-value").textContent = "Processing";
    byId("request-value").textContent = state.activeRequestId;
    const result = await waitForRequest(response.interface_request_id);
    const responseRole = result.response_type === "tool" ? "tool" : result.response_type === "planning" ? "planning" : "assistant";
    const content = String(result.content || "").trim() || (result.errors || []).join("\n") || "JARVIS returned an empty response. Retry or select another provider.";
    appendMessage(responseRole, content, result, result.status);
    updateExecutionMetadata(result);
    await Promise.all([loadConversations(), loadActivity(), loadApprovals(), loadStatus()]);
    if (result.command_name && result.command_name.startsWith("voice")) await loadVoice();
  } catch (error) {
    appendMessage("assistant", error.message, {}, "failed");
    if (!accepted || !byId("message-input").value) byId("message-input").value = text;
    resizeComposer();
    setAssistantState("error", "Request failed");
    showToast(error.message);
  } finally {
    state.activeRequestId = null;
    setPending(false);
    byId("message-input").readOnly = false;
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
  byId("provider-dot").className = `status-dot ${result.status === "completed" ? "healthy" : result.status === "failed" ? "failed" : "processing"}`;
  byId("execution-status").textContent = result.status || "Completed";
  byId("request-value").textContent = result.jarvis_request_id || result.interface_request_id || "Awaiting input";
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
  restoreWelcome("New conversation", "A clean intelligence channel is ready.");
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
  document.body.classList.remove("rail-open");
  byId("rail-scrim").hidden = true;
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
  data.activity.forEach(ingestActivity);
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
  byId("rail-voice-label").textContent = voice.output_enabled ? "Enabled" : "Disabled";
  const microphone = byId("microphone-button");
  microphone.disabled = !voice.microphone_available || !voice.input_enabled;
  microphone.title = microphone.disabled ? "Voice input is not available" : "Start voice input";
  microphone.setAttribute("aria-label", microphone.title);
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
  state.speaking = true; setAssistantState("speaking", "Speaking");
  try {
    const result = await api("/api/voice/speak", { method: "POST", body: JSON.stringify({ text }) });
    showToast(result.status === "completed" ? "Voice synthesis completed" : `Voice: ${result.status}`);
    await loadActivity();
  } catch (error) { setAssistantState("error", "Voice output failed"); showToast(error.message); }
  finally { state.speaking = false; if (state.connected && !state.activeRequestId) setAssistantState("idle", "System ready"); await loadVoice().catch(() => {}); }
}

async function stopVoice() {
  try { const result = await api("/api/voice/stop", { method: "POST", body: "{}" }); state.speaking = false; setAssistantState("idle", "System ready"); showToast(result.stopped ? "Voice stopped" : "No active speech output"); }
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
  const fieldLabel = document.createElement("label"); fieldLabel.className = "switch-field";
  const copy = document.createElement("span"); copy.textContent = label;
  const control = document.createElement("span"); control.className = "switch-control";
  const input = document.createElement("input"); input.type = "checkbox"; input.checked = Boolean(current); input.setAttribute("role", "switch");
  const track = document.createElement("span"); track.className = "switch-track"; track.setAttribute("aria-hidden", "true");
  input.addEventListener("change", () => updateSetting(section, key, input.checked));
  control.append(input, track); fieldLabel.append(copy, control); wrapper.append(fieldLabel); return wrapper;
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
  byId("provider-dot").className = `status-dot ${status.runtime === "running" ? "healthy" : "unavailable"}`;
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

function ingestActivity(record) {
  const sequence = Number(record.sequence || 0);
  const key = sequence ? `sequence:${sequence}` : [record.event_type, record.request_id, record.created_at].join(":");
  if (state.seenEvents.has(key)) return false;
  state.seenEvents.add(key);
  if (state.seenEvents.size > 500) state.seenEvents.delete(state.seenEvents.values().next().value);
  state.lastEventSequence = Math.max(state.lastEventSequence, sequence);
  byId("stage-value").textContent = record.summary || record.event_type?.replaceAll("_", " ") || "Active";
  byId("request-value").textContent = record.request_id || "Awaiting input";
  if (record.provider_id) { byId("provider-value").textContent = record.provider_id; byId("provider-dot").className = "status-dot healthy"; }
  if (record.model_id) byId("model-value").textContent = record.model_id;
  if (record.invocation_id) byId("tool-value").textContent = record.invocation_id;
  if (record.coordination_id) byId("coordination-value").textContent = record.coordination_id;
  if (record.plan_id) byId("plan-value").textContent = record.plan_id;
  const eventType = String(record.event_type || "");
  if (eventType.includes("voice_synthesis_started")) { state.speaking = true; setAssistantState("speaking", "Speaking"); }
  else if (eventType.includes("voice_synthesis_completed") || eventType.includes("voice_stopped")) { state.speaking = false; if (!state.activeRequestId) setAssistantState("idle", "System ready"); }
  else if (["accepted", "processing", "running"].includes(record.status) || /(started|selected|validated)$/.test(eventType)) setAssistantState("thinking", record.summary || "Reasoning");
  else if (["failed", "rejected", "unavailable"].includes(record.status)) setAssistantState("error", record.summary || "Attention required");
  else if (["completed", "cancelled"].includes(record.status) && !state.activeRequestId && !state.speaking) setAssistantState("idle", "System ready");
  return true;
}

function scheduleEventReconnect() {
  if (state.eventTimer) clearTimeout(state.eventTimer);
  const delay = Math.min(15000, 1000 * (2 ** Math.min(state.reconnectAttempt, 4)));
  state.reconnectAttempt += 1;
  setConnection("reconnecting", `Connection interrupted. Retrying in ${Math.ceil(delay / 1000)}s...`);
  state.eventTimer = setTimeout(connectEvents, delay);
}

async function pollEvents() {
  try {
    await loadActivity();
    state.reconnectAttempt = 0; setConnection("online");
    state.eventTimer = setTimeout(pollEvents, 2500);
  } catch {
    if (state.reconnectAttempt >= 6) setConnection("offline");
    scheduleEventReconnect();
  }
}

function connectEvents() {
  if (state.eventSource) { state.eventSource.close(); state.eventSource = null; }
  if (typeof window.EventSource !== "function") { pollEvents(); return; }
  const source = new EventSource(`/api/events?since=${state.lastEventSequence}`);
  state.eventSource = source;
  source.onopen = () => { state.reconnectAttempt = 0; setConnection("online"); };
  source.addEventListener("activity", (event) => {
    try { if (ingestActivity(JSON.parse(event.data))) loadActivity().catch(() => {}); }
    catch { showToast("An activity update could not be read."); }
  });
  source.onerror = () => { source.close(); if (state.eventSource === source) state.eventSource = null; scheduleEventReconnect(); };
}

function bindEvents() {
  byId("composer").addEventListener("submit", (event) => { event.preventDefault(); sendMessage(byId("message-input").value); });
  byId("message-input").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); byId("composer").requestSubmit(); } });
  byId("message-input").addEventListener("input", resizeComposer);
  byId("messages").addEventListener("scroll", () => { const container = byId("messages"); state.autoScroll = container.scrollHeight - container.scrollTop - container.clientHeight < 72; if (state.autoScroll) byId("scroll-latest").hidden = true; });
  byId("scroll-latest").addEventListener("click", () => { state.autoScroll = true; byId("scroll-latest").hidden = true; byId("messages").scrollTo({ top: byId("messages").scrollHeight, behavior: "smooth" }); });
  byId("cancel-request").addEventListener("click", cancelActive);
  byId("new-conversation").addEventListener("click", newConversation);
  byId("refresh-history").addEventListener("click", loadConversations);
  byId("refresh-approvals").addEventListener("click", loadApprovals);
  byId("theme-toggle").addEventListener("click", () => updateSetting("interface", "theme", document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
  byId("sidebar-toggle").addEventListener("click", () => { byId("sidebar").classList.add("open"); document.body.classList.add("rail-open"); byId("rail-scrim").hidden = false; });
  const closeRail = () => { byId("sidebar").classList.remove("open"); document.body.classList.remove("rail-open"); byId("rail-scrim").hidden = true; };
  byId("rail-close").addEventListener("click", closeRail); byId("rail-scrim").addEventListener("click", closeRail);
  byId("activity-toggle").addEventListener("click", () => { const open = !byId("activity-panel").classList.contains("open"); byId("activity-panel").classList.toggle("open", open); document.body.classList.toggle("context-open", open); byId("panel-scrim").hidden = !open; });
  const closeContext = () => { byId("activity-panel").classList.remove("open"); document.body.classList.remove("context-open"); byId("panel-scrim").hidden = true; };
  byId("close-activity").addEventListener("click", closeContext); byId("panel-scrim").addEventListener("click", closeContext);
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
    if (state.activeConversationId) {
      const current = await api(`/api/conversations/${encodeURIComponent(state.activeConversationId)}`);
      if (current.status === "completed" && current.messages?.length) {
        byId("messages").replaceChildren(); current.messages.forEach((message) => appendMessage(message.role, message.content, message.metadata || {}, message.status));
      }
    }
    setConnection("online"); setAssistantState("idle", "System ready");
    connectEvents();
  } catch (error) {
    byId("runtime-label").textContent = "Unavailable";
    byId("runtime-dot").className = "status-dot unavailable";
    showToast(`Interface startup failed: ${error.message}`);
    setConnection("offline", `Interface startup failed: ${error.message}`);
  }
}

window.addEventListener("beforeunload", () => { state.eventSource?.close(); if (state.eventTimer) clearTimeout(state.eventTimer); if (state.requestTimer) clearInterval(state.requestTimer); });
initialize();
