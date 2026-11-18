"use strict";

const $ = id => document.getElementById(id);
const node = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text != null) element.textContent = text;
  if (className) element.className = className;
  return element;
};
const button = (text, action, className) => {
  const element = node("button", text, className);
  element.type = "button";
  element.addEventListener("click", action);
  return element;
};
const option = (text, value) => new Option(text, value);
const heading = (text, level = "h2") => node(level, text);
const capital = value => value ? value[0].toUpperCase() + value.slice(1) : "";
const date = value => value ? new Date(value).toLocaleString() : "—";
const number = value => Number(value ?? 0).toLocaleString();
const endpointLabel = entry => {
  if (!entry) return "";
  if (entry.simulated_local) return `${entry.model} · Cloud (local stand-in)`;
  if (entry.subscription) return `${entry.model} · Cloud (Codex subscription)`;
  return `${entry.model} · ${capital(entry.location) || "Location unavailable"}`;
};
const freshDraft = () => ({text: "", agent: "", models: {}, documents: {}, previous: false, pending: null});
const state = {
  index: null, view: "chat", chat: "", reply: "", run: "", rows: [], detail: null, os: null, process: "",
  filter: "all", sort: "", direction: 1, generation: 0, polling: false, sending: false,
  drafts: new Map(), transcriptKey: "", chatsKey: "", runKey: "", monitorKey: "",
};

function fieldMessage(id, text) {
  $(id).textContent = text;
  $(id).hidden = !text;
}

async function api(path = "", body) {
  const response = await fetch("/api/workspace" + path, {
    ...(body ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)} : {}),
    signal: AbortSignal.timeout(15000),
  });
  const value = await response.json();
  if (!response.ok) {
    const error = new Error(value.error || "Workspace request failed");
    error.rejected = response.status >= 400 && response.status < 500;
    throw error;
  }
  return value;
}

function draft() {
  if (!state.drafts.has(state.chat)) state.drafts.set(state.chat, freshDraft());
  return state.drafts.get(state.chat);
}

function agent() {
  return state.index?.agents.find(item => item.id === draft().agent);
}

function modelChoices() {
  return (agent()?.fields || []).map(field =>
    field.options.find(model => model.id === draft().models[field.role] && !model.disabled_reason));
}

function renderComposer() {
  const active = draft();
  const agents = state.index?.agents || [];
  const available = item => !item.disabled_reason && item.fields.every(
    field => field.options.some(model => !model.disabled_reason));
  if (!active.agent) active.agent = (agents.find(available) || agents[0])?.id || "";
  const agentSelect = $("agent");
  agentSelect.replaceChildren(...agents.map(item => {
    const entry = option(item.name + (available(item) ? "" : " (unavailable)"), item.id);
    entry.title = item.description;
    return entry;
  }));
  agentSelect.value = active.agent;
  $("models").replaceChildren();
  const item = agent();
  for (const field of item?.fields || []) {
    const label = node("label", field.role === "general" ? "Model" : field.label, "control");
    const select = node("select");
    const placeholder = option("Choose a model", "");
    placeholder.disabled = true;
    select.append(placeholder);
    for (const model of field.options) {
      const entry = option(endpointLabel(model) + (model.disabled_reason ? ` (${model.disabled_reason})` : ""), model.id);
      entry.disabled = Boolean(model.disabled_reason);
      select.append(entry);
    }
    const saved = active.models[field.role];
    active.models[field.role] = field.options.some(model => model.id === saved && !model.disabled_reason)
      ? saved : (field.default || "");
    select.value = active.models[field.role];
    select.disabled = !field.options.some(model => !model.disabled_reason);
    select.addEventListener("change", () => {
      active.models[field.role] = select.value;
      updateComposer();
    });
    label.append(select);
    $("models").append(label);
  }
  $("message").value = active.text;
  $("include-previous").checked = active.previous;
  updateComposer();
}

function updateComposer() {
  const active = draft();
  const item = agent();
  const choices = modelChoices();
  const files = Object.keys(active.documents);
  const ready = state.index && item && !item.disabled_reason && choices.every(Boolean);
  const priorComplete = state.rows.at(-1)?.status === "completed";
  // A lost acknowledgement is retried with its original payload and identity.
  const pending = Boolean(active.pending);
  $("message").readOnly = pending;
  $("agent").disabled = pending || !state.index;
  for (const select of $("models").querySelectorAll("select")) {
    select.disabled = pending || !Array.from(select.options).some(entry => !entry.disabled && entry.value);
  }
  $("attach").disabled = pending;
  $("clear-files").disabled = pending;
  $("include-previous").disabled = pending;
  $("context-option").hidden = !priorComplete && !active.previous;
  $("files-summary").textContent = files.join(", ");
  $("clear-files").hidden = !files.length;
  $("send").disabled = state.sending || (!pending && (!ready || !active.text.trim()
    || Boolean(state.index?.active) || Boolean(state.index?.blocked)));
  $("send").textContent = state.sending ? "Sending…" : pending ? "Confirm send" : "Send";
  const locations = [...new Set(choices.filter(Boolean).map(model => capital(model.location)))];
  $("destination").textContent = locations.length
    ? `${files.length ? "Prompts and selected document excerpts" : "Prompts"} · ${locations.join(" + ")} inference`
    : item?.description || "";
  const missing = item?.fields.find((_, index) => !choices[index]);
  const reason = item?.disabled_reason || (missing && (
    missing.options[0]?.disabled_reason || `Choose a compatible model for ${missing.label.toLowerCase()}.`));
  const blocker = state.index?.blocked ? "A prior invocation has unresolved effects or resource holds."
    : state.index?.active ? "An invocation is in progress in this workspace." : "";
  fieldMessage("send-status", pending && !state.sending
    ? "The send acknowledgement was lost. Confirm send checks the original request." : blocker || reason || "");
}

function renderSidebar() {
  const chats = state.index?.chats || [];
  const key = JSON.stringify([state.chat, chats]);
  if (state.chatsKey === key) return;
  state.chatsKey = key;
  const items = chats.map(chat => {
    const item = button(chat.title, () => openChat(chat.id), "chat-item");
    item.title = chat.title;
    if (chat.id === state.chat) item.setAttribute("aria-current", "true");
    return item;
  });
  if (!items.length) items.push(node("p", "No conversations yet.", "empty-table"));
  $("chat-list").replaceChildren(...items);
  $("chat-title").textContent = chats.find(chat => chat.id === state.chat)?.title || "New chat";
}

function selectView(view) {
  state.view = view;
  state.generation++;
  for (const item of document.querySelectorAll("[data-view]")) {
    if (item.dataset.view === view) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
    $(item.dataset.view + "-view").hidden = item.dataset.view !== view;
  }
  render();
  void refresh();
}

function openChat(id, reply = "") {
  state.chat = id;
  state.reply = reply;
  state.rows = [];
  fieldMessage("send-error", "");
  renderComposer();
  selectView("chat");
  if (!reply) $("message").focus();
}

function openRun(id, view, binding = "", process = "") {
  state.run = id;
  state.detail = null;
  state.process = process;
  state.filter = "all";
  $("search").value = "";
  $("binding").value = binding;
  selectView(view);
  $(view + "-title").focus();
}

function renderChat() {
  const detail = state.detail?.live ? state.detail : null;
  const key = JSON.stringify([state.chat, state.rows, detail?.processes.map(({id, status}) => [id, status])]);
  if (key === state.transcriptKey && !state.reply) return;
  state.transcriptKey = key;
  const transcript = $("transcript");
  const follow = transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight < 90;
  const focusRun = document.activeElement?.dataset?.run;
  const messages = state.rows.map(turn => {
    const article = node("article", null, "turn");
    article.dataset.invocation = turn.id;
    article.tabIndex = -1;
    const message = node("div", null, "user-message");
    message.append(node("p", turn.text, "message-text"));
    if (turn.documents.length) message.append(node("p", turn.documents.join(", "), "reply-meta"));
    const reply = node("div", null, "agent-reply");
    const header = node("div", null, "reply-heading");
    header.append(heading(capital(turn.agent)), node("span",
      Object.values(turn.models).map(endpointLabel).join(" / "), "reply-meta"));
    reply.append(header);
    if (turn.answer) reply.append(node("p", turn.answer, "message-text"));
    else {
      const current = detail?.id === turn.id && detail.processes.find(process =>
        process.category === "running" || process.category === "waiting");
        const line = turn.error || (current ? `${current.name} · ${current.status}`
        : turn.status === "running" ? "Invocation in progress…" : capital(turn.status));
      reply.append(node("p", line, turn.error ? "form-error" : "message-text"));
    }
    const actions = node("div", null, "reply-actions");
    const inspect = button("View processes", () => openRun(turn.id, "agents"), "quiet");
    inspect.dataset.run = turn.id;
    actions.append(inspect, node("span", date(turn.created_at), "reply-meta"));
    reply.append(actions);
    article.append(message, reply);
    return article;
  });
  if (!messages.length) {
    const empty = node("div", null, "empty");
    empty.append(heading(state.chat ? "Loading conversation…" : "What would you like to work on?"));
    messages.push(empty);
  }
  transcript.replaceChildren(...messages);
  const reply = state.reply && messages.find(message => message.dataset.invocation === state.reply);
  if (reply) {
    state.reply = "";
    reply.scrollIntoView({block: "nearest"});
    reply.focus({preventScroll: true});
  } else if (follow) transcript.scrollTop = transcript.scrollHeight;
  if (!reply && focusRun) Array.from(transcript.querySelectorAll("button")).find(
    item => item.dataset.run === focusRun)?.focus({preventScroll: true});
}

function renderRunChoices() {
  const runs = state.index?.runs || [];
  if (!runs.some(run => run.id === state.run)) state.run = runs[0]?.id || "";
  const key = JSON.stringify([state.run, runs]);
  if (key === state.runKey) return;
  state.runKey = key;
  const select = $("agents-run");
  select.replaceChildren(...(runs.length ? runs.map(run => option(
    `${run.title} · ${capital(run.agent)} · ${date(run.created_at)}`, run.id))
    : [option("No invocations", "")]));
  select.value = state.run;
  select.disabled = !runs.length;
}

function observation(detail) {
  if (!detail) return state.run ? "Loading invocation…" : "Send a chat message to create an invocation.";
  if (!detail.observed) return "No OS records for this invocation yet.";
  return `${detail.live ? "Observed" : "Retained records inspected"} at ${date(detail.captured_at)} · Per invocation`;
}

function definitions(values) {
  const list = node("dl");
  for (const [label, value] of values) list.append(node("dt", label), node("dd", value ?? "—"));
  return list;
}

function renderOS() {
  const detail = state.os;
  const capture = detail ? `Observed at ${date(detail.captured_at)} · Workspace journals ${detail.journals} of ${detail.invocations}`
    : "Loading workspace status…";
  const key = JSON.stringify(detail && {...detail, captured_at: null});
  const surface = $("os-data");
  if (state.monitorKey === key && surface.firstElementChild) {
    surface.firstElementChild.textContent = capture;
    return;
  }
  state.monitorKey = key;
  const content = [node("p", capture, "observation")];
  if (detail) {
    const summary = node("article", null, "holds");
    const {process_counts: processes, effect_counts: effects} = detail;
    const hasRetainedHolds = detail.holds.some(hold => !hold.live) || detail.unresolved.length;
    const status = detail.active ? "Invoking agent" : hasRetainedHolds ? "Awaiting reconciliation"
      : detail.unavailable.length ? "Incomplete observation" : "Idle";
    summary.append(heading("System status"), definitions([
      ["Workspace", status],
      ["Invocations", number(detail.invocations)],
      ["Processes", `${number(processes.Running)} running · ${number((processes.Waiting || 0)
        + (processes["Waiting for resource"] || 0))} waiting · ${number(processes.Paused)} paused · ${number(processes.Finished)} finished`],
      ["Operations", `${number((effects.submitting || 0) + (effects.active || 0))} in flight · ${number(effects.succeeded)} succeeded · ${number(effects.failed)} failed · ${number(effects.Unconfirmed)} unconfirmed`],
    ]));
    if (detail.unavailable.length) summary.append(node("p",
      `${detail.unavailable.length} invocation journal(s) could not be read. Totals are partial.`, "form-error"));
    content.push(summary);
    const lanes = node("div", null, "lanes");
    for (const lane of detail.lanes) {
      const card = node("article", null, "lane");
      card.append(heading(`${capital(lane.name)} binding`), node("p", endpointLabel(lane) || "Unavailable", "lane-model"),
        node("p", `${number(lane.held)} / ${lane.limit ?? "—"}`, "lane-value"),
        node("p", "Live reserved inference slots / configured slots", "reply-meta"));
      if (lane.limit > 0) {
        const meter = node("progress");
        meter.max = lane.limit;
        meter.value = lane.held;
        meter.setAttribute("aria-label", `${capital(lane.name)} reserved slots`);
        card.append(meter);
      }
      card.append(definitions([
        ["Declared location", capital(lane.location) || "Unavailable"],
        ["Live waiters", number(lane.ordinary_waiters + lane.finishing_waiters)],
        ["Live reserved tokens", number(lane.reserved_tokens)],
        ["Retained slots held", number(lane.retained_held)],
        ["Token capacity", lane.token_limit_owner === "provider" ? "Provider managed" : number(lane.token_limit)],
        ["Reported tokens · retained records", number(lane.reported_tokens)],
        ["Submitted attempts without a token report", number(lane.unreported_attempts)],
      ]));
      if (lane.latest_run) card.append(button("Latest binding processes", () => openRun(lane.latest_run, "agents", lane.name)));
      lanes.append(card);
    }
    content.push(lanes, node("p", "Capacity is the workspace launch configuration. Shared provider quotas and external workloads are unavailable.", "observation"));
    const holds = node("article", null, "holds");
    holds.append(heading("Resource holds"));
    if (!detail.holds.length) holds.append(node("p", "No retained resource holds.", "observation"));
    const list = node("ul");
    for (const hold of detail.holds) {
      const li = node("li");
      li.append(button(`${hold.live ? "Live" : "Retained"} · ${capital(hold.binding) || "Permission"} · ${hold.run_id.slice(0, 8)} · ${hold.process_id || hold.id}`,
        () => openRun(hold.run_id, "agents", hold.binding || "", hold.process_id || "")));
      list.append(li);
    }
    if (list.childElementCount) holds.append(list);
    for (const effect of detail.unresolved) {
      holds.append(button(`Execution unconfirmed · ${effect.run_id.slice(0, 8)} · ${effect.id}`,
        () => openRun(effect.run_id, "agents", "", effect.process_id)));
    }
    content.push(holds);
  }
  surface.replaceChildren(...content);
}

function statusBadge(process) {
  const glyphs = {running: "●", waiting: "◷", finished: "■", preempted: "Ⅱ"};
  const badge = node("span", null, `status ${process.category}`);
  const icon = glyphs[process.category];
  if (icon) {
    const marker = node("span", icon);
    marker.setAttribute("aria-hidden", "true");
    badge.append(marker);
  }
  badge.append(process.status);
  return badge;
}

function renderInspector(process) {
  const panel = $("process-detail");
  if (!process) {
    panel.replaceChildren(heading("Process details"), node("p", "Select a process in the table."));
    return;
  }
  const detail = state.detail;
  const items = [heading(process.name), node("p", process.id, "mono"), statusBadge(process)];
  if (process.unconfirmed) items.push(node("p", "Execution unconfirmed", "status warning"));
  items.push(definitions([
    ["Role", process.role], ["Parent", process.parent], ["Configured model", process.model],
    ["Binding", process.binding], ["Reason", process.reason], ["Started", date(process.started_at)],
    ["Finished", date(process.finished_at)], ["Cleanup", process.cleanup],
  ]));
  if (process.wait?.since) items.push(node("p", `Waiting since ${date(process.wait.since)}`));
  if (process.wait?.targets?.length) items.push(node("p", `Waiting for ${process.wait.targets.join(", ")}`));
  if (process.reservations.length || process.permits.length) {
    items.push(node("p", `Resource references · ${[...process.reservations, ...process.permits].join(", ")}`));
  }
  items.push(heading("Recorded operations", "h3"));
  if (!process.attempts.length) items.push(node("p", "No operation records yet."));
  for (const attempt of process.attempts) {
    const row = node("div", null, "attempt");
    row.append(node("strong", `${attempt.kind?.replaceAll("_", " ") || "Operation"} · ${attempt.state}`),
      node("p", attempt.id, "mono"), node("p", date(attempt.at)));
    if (attempt.model) row.append(node("p", `${attempt.confirmed ? "Recorded" : "Attempted"} model · ${attempt.model}`));
    if (attempt.location) row.append(node("p", `Recorded location · ${attempt.location}`));
    if (attempt.session) row.append(node("p", `Provider session · ${attempt.session}`, "mono"));
    if (attempt.error_kind) row.append(node("p", `Failure · ${attempt.error_kind}`, "form-error"));
    items.push(row);
  }
  items.push(button("View reply", () => openChat(detail.chat_id, detail.id)),
    button("View OS resources", () => {
      selectView("os");
      $("os-title").focus();
    }));
  panel.replaceChildren(...items);
}

let processKey = "";
function renderProcesses() {
  const detail = state.detail;
  const search = $("search").value.trim().toLowerCase();
  const binding = $("binding").value;
  const processes = (detail?.processes || []).filter(process =>
    (!binding || process.binding === binding) &&
    (!search || [process.name, process.step, process.id, process.model, process.role, detail.title].some(
      value => value?.toLowerCase().includes(search))));
  const counts = processes.reduce((result, process) => {
    result[process.category] = (result[process.category] || 0) + 1;
    return result;
  }, {all: processes.length});
  const labels = {all: "All", running: "Running", preempted: "Preempted", waiting: "Waiting", finished: "Finished"};
  for (const item of document.querySelectorAll("[data-filter]")) {
    const key = item.dataset.filter;
    item.setAttribute("aria-pressed", String(key === state.filter));
    item.textContent = item.disabled ? labels[key] : `${labels[key]} ${counts[key] || 0}`;
  }
  for (const item of document.querySelectorAll("[data-sort]")) {
    if (item.dataset.sort === state.sort) {
      item.parentNode.setAttribute("aria-sort", state.direction === 1 ? "ascending" : "descending");
    } else item.parentNode.removeAttribute("aria-sort");
  }
  $("agents-observation").textContent = observation(detail) + " · Scheduler preemption is unavailable.";
  const rows = processes.filter(process => state.filter === "all" || state.filter === process.category);
  const order = {running: 0, waiting: 1, preempted: 2, other: 3, finished: 4};
  rows.sort((a, b) => state.sort ? state.direction * String(a[state.sort] || "").localeCompare(String(b[state.sort] || ""))
    : order[a.category] - order[b.category] || String(a.started_at || "").localeCompare(String(b.started_at || "")));
  const selected = rows.find(process => process.id === state.process);
  const key = JSON.stringify([state.run, rows, state.process, state.filter]);
  if (processKey === key) return;
  processKey = key;
  const focused = document.activeElement?.dataset?.process;
  const content = rows.map(process => {
    const row = node("tr", null, process === selected ? "selected" : "");
    const name = button(process.name, () => {
      state.process = process.id;
      renderProcesses();
    }, "process-name");
    name.dataset.process = process.id;
    name.setAttribute("aria-pressed", String(process === selected));
    const title = node("td");
    title.append(name);
    const status = node("td");
    status.append(statusBadge(process));
    const reason = process.unconfirmed ? `${process.reason} · Execution unconfirmed` : process.reason;
    row.append(title, node("td", capital(process.binding) || "—"), status,
      node("td", date(process.started_at), "mono"), node("td", reason));
    return row;
  });
  $("process-rows").replaceChildren(...content);
  if (focused) Array.from($("process-rows").querySelectorAll("button")).find(
    item => item.dataset.process === focused)?.focus({preventScroll: true});
  const empty = $("process-empty");
  empty.hidden = Boolean(rows.length);
  empty.textContent = detail?.processes.length ? "No processes match these filters."
    : detail ? "No processes have been recorded." : state.run ? "Loading invocation…" : "No invocations yet.";
  renderInspector(selected);
}

function render() {
  renderSidebar();
  renderRunChoices();
  if (state.view === "chat") {
    renderChat();
    updateComposer();
  } else if (state.view === "os") renderOS();
  else renderProcesses();
}

async function refresh() {
  if (state.polling) return;
  state.polling = true;
  const generation = state.generation;
  try {
    const index = await api();
    if (generation !== state.generation) return;
    const priorAgents = JSON.stringify(state.index?.agents);
    state.index = index;
    if (JSON.stringify(index.agents) !== priorAgents) renderComposer();
    renderRunChoices();
    if (state.view === "chat" && state.chat) {
      const rows = await api("/chat?id=" + encodeURIComponent(state.chat));
      if (generation !== state.generation) return;
      state.rows = rows;
    }
    if (state.view === "os") {
      const observation = await api("/os");
      if (generation !== state.generation) return;
      state.os = observation;
    } else {
      const id = state.view === "chat"
        ? state.rows.find(run => run.id === index.active)?.id : state.run;
      const detail = id ? await api("/invocation?id=" + encodeURIComponent(id)) : null;
      if (generation !== state.generation) return;
      state.detail = detail;
    }
    $("connection").textContent = "Connected";
    fieldMessage("app-error", "");
    render();
  } catch (error) {
    if (generation !== state.generation) return;
    $("connection").textContent = "Connection interrupted";
    fieldMessage("app-error", `Could not refresh the workspace. ${error.message}`);
  } finally {
    state.polling = false;
    if (generation !== state.generation) void refresh();
  }
}

for (const item of document.querySelectorAll("[data-view]")) {
  item.addEventListener("click", () => {
    if (state.view !== item.dataset.view) {
      state.detail = null;
      selectView(item.dataset.view);
    }
  });
}
$("agents-run").addEventListener("change", event => openRun(event.target.value, "agents"));
for (const item of document.querySelectorAll("[data-filter]")) {
  item.addEventListener("click", () => { state.filter = item.dataset.filter; renderProcesses(); });
}
for (const item of document.querySelectorAll("[data-sort]")) {
  item.addEventListener("click", () => {
    state.direction = state.sort === item.dataset.sort ? -state.direction : 1;
    state.sort = item.dataset.sort;
    renderProcesses();
  });
}
$("search").addEventListener("input", renderProcesses);
$("binding").addEventListener("change", renderProcesses);
$("new-chat").addEventListener("click", () => openChat(""));
$("agent").addEventListener("change", event => {
  draft().agent = event.target.value;
  draft().models = {};
  renderComposer();
});
$("message").addEventListener("input", event => { draft().text = event.target.value; updateComposer(); });
$("include-previous").addEventListener("change", event => { draft().previous = event.target.checked; });
$("attach").addEventListener("click", () => $("files").click());
$("clear-files").addEventListener("click", () => { draft().documents = {}; updateComposer(); });
$("files").addEventListener("change", async event => {
  const active = draft();
  const files = [...event.target.files];
  event.target.value = "";
  if (!files.length) return;
  try {
    if (files.length > 64 || files.some(file => file.name.length > 128)
        || files.reduce((sum, file) => sum + file.size, 0) > 128000) {
      throw new Error("Choose up to 64 text documents totaling at most 128 KB, with names up to 128 characters.");
    }
    const contents = await Promise.all(files.map(async file => [
      file.name, new TextDecoder("utf-8", {fatal: true}).decode(await file.arrayBuffer()),
    ]));
    if (new Set(contents.map(([name]) => name)).size !== contents.length) {
      throw new Error("Use distinct names for the attached documents.");
    }
    if (active.pending) return;
    active.documents = Object.fromEntries(contents);
    if (active === draft()) {
      fieldMessage("send-error", "");
      updateComposer();
    }
  } catch (error) {
    if (active === draft()) fieldMessage("send-error", error.message);
  }
});
$("composer").addEventListener("submit", async event => {
  event.preventDefault();
  if ($("send").disabled) return;
  const currentChat = state.chat;
  const active = draft();
  active.pending ||= {
    id: crypto.randomUUID().replaceAll("-", ""), chat_id: currentChat || null, text: active.text,
    agent: active.agent, models: {...active.models}, documents: active.documents, include_previous: active.previous,
  };
  state.sending = true;
  fieldMessage("send-error", "");
  updateComposer();
  try {
    const ack = await api("/send", active.pending);
    const savedDraft = {...freshDraft(), agent: active.agent, models: active.models};
    state.drafts.set(ack.chat_id, savedDraft);
    if (!currentChat) state.drafts.delete(currentChat);
    if (currentChat === state.chat) {
      state.generation++;
      state.chat = ack.chat_id;
      renderComposer();
    }
  } catch (error) {
    if (error.rejected) active.pending = null;
    if (currentChat === state.chat) fieldMessage("send-error", error.message);
  } finally {
    state.sending = false;
    updateComposer();
    void refresh();
  }
});

void refresh();
setInterval(() => { if (!document.hidden) void refresh(); }, 1600);
document.addEventListener("visibilitychange", () => { if (!document.hidden) void refresh(); });
