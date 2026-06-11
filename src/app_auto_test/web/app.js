const state = {
  health: null,
  devices: [],
  runs: [],
  sample: null,
  currentRun: null,
  pollTimer: null,
};

const nodes = {};

document.addEventListener("DOMContentLoaded", () => {
  bindNodes();
  bindEvents();
  refreshAll();
});

function bindNodes() {
  const ids = [
    "apiStatus",
    "refreshButton",
    "executionMode",
    "runForm",
    "testName",
    "apkFile",
    "packageName",
    "testGoal",
    "deviceSelect",
    "generateButton",
    "createButton",
    "checkCapabilityButton",
    "deviceCount",
    "deviceList",
    "capabilityReady",
    "capabilityPanel",
    "sampleStatus",
    "flowEditor",
    "exportHtmlButton",
    "exportJsonButton",
    "runSummary",
    "runCount",
    "runList",
    "eventCount",
    "eventList",
    "reportStatus",
    "reportView",
    "toast",
  ];
  ids.forEach((id) => {
    nodes[id] = document.getElementById(id);
  });
}

function bindEvents() {
  nodes.refreshButton.addEventListener("click", refreshAll);
  nodes.generateButton.addEventListener("click", generateSample);
  nodes.checkCapabilityButton.addEventListener("click", checkCapability);
  nodes.runForm.addEventListener("submit", createRun);
  nodes.exportHtmlButton.addEventListener("click", () => exportReport("html"));
  nodes.exportJsonButton.addEventListener("click", () => exportReport("json"));
  nodes.deviceSelect.addEventListener("change", checkCapability);
  nodes.packageName.addEventListener("change", checkCapability);
  document.querySelectorAll("input[name='platform']").forEach((input) => {
    input.addEventListener("change", handlePlatformChange);
  });
}

async function refreshAll() {
  setBusy(nodes.refreshButton, true, "Refreshing");
  try {
    await Promise.all([loadHealth(), loadDevices(), loadRuns()]);
    await checkCapability({ silent: true });
    const savedRunId = localStorage.getItem("app-auto-test:last-run-id");
    const selectedRun = state.runs.find((run) => run.run_id === savedRunId) || state.runs[0];
    if (selectedRun) {
      await selectRun(selectedRun.run_id);
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.refreshButton, false, "Refresh");
  }
}

async function loadHealth() {
  const response = await api("/api/v1/health");
  state.health = response.data;
  nodes.apiStatus.textContent = state.health.status === "ok" ? "API online" : "API unavailable";
  nodes.apiStatus.className = `status-pill ${state.health.status === "ok" ? "ready" : "blocked"}`;
  nodes.executionMode.textContent = state.health.realExecutionEnabled ? "Real execution on" : "Real execution off";
  nodes.executionMode.className = `status-pill ${state.health.realExecutionEnabled ? "ready" : "warning"}`;
}

async function loadDevices() {
  const platform = getSelectedPlatform();
  const response = await api(`/api/v1/devices?platform=${encodeURIComponent(platform)}`);
  state.devices = response.data.items || [];
  renderDeviceSelect();
  renderDevices();
}

async function loadRuns() {
  const response = await api("/api/v1/runs");
  state.runs = response.data.items || [];
  renderRuns();
}

function renderDeviceSelect() {
  const previous = nodes.deviceSelect.value;
  clear(nodes.deviceSelect);
  state.devices.forEach((device) => {
    const option = document.createElement("option");
    option.value = device.id;
    option.textContent = `${device.name} (${device.kind}, ${device.status})`;
    option.disabled = !device.selectable;
    nodes.deviceSelect.appendChild(option);
  });
  const selectable = state.devices.find((device) => device.selectable);
  const previousStillExists = state.devices.find((device) => device.id === previous);
  if (previousStillExists) {
    nodes.deviceSelect.value = previous;
  } else if (selectable) {
    nodes.deviceSelect.value = selectable.id;
  }
}

function renderDevices() {
  nodes.deviceCount.textContent = `${state.devices.length} target${state.devices.length === 1 ? "" : "s"}`;
  clear(nodes.deviceList);
  if (!state.devices.length) {
    nodes.deviceList.append(empty("No devices returned."));
    return;
  }
  state.devices.forEach((device) => {
    const item = document.createElement("article");
    item.className = "device-item";

    const body = document.createElement("div");
    const title = document.createElement("div");
    title.className = "title-line";
    title.append(textSpan(device.name));
    title.append(tag(device.selectable ? "Selectable" : "Blocked", device.selectable ? "ready" : "blocked"));
    body.append(title);

    const details = document.createElement("div");
    details.className = "details";
    details.textContent = [device.platform, device.kind, device.serial || device.id, device.blocked_reason]
      .filter(Boolean)
      .join(" | ");
    body.append(details);

    item.append(body);
    item.append(tag(device.status, statusClass(device.status)));
    nodes.deviceList.append(item);
  });
}

async function handlePlatformChange() {
  const platform = getSelectedPlatform();
  nodes.createButton.textContent = platform === "ios" ? "Check iOS capability" : "Create run";
  nodes.apkFile.disabled = platform === "ios";
  await loadDevices();
  await checkCapability({ silent: true });
}

async function checkCapability(options = {}) {
  const platform = getSelectedPlatform();
  const form = new FormData();
  form.append("platform", platform);
  form.append("device_id", nodes.deviceSelect.value || "");
  form.append("package_name", nodes.packageName.value.trim());
  form.append("apk_path", nodes.apkFile.files[0] ? nodes.apkFile.files[0].name : "");

  setBusy(nodes.checkCapabilityButton, true, "Checking");
  try {
    const response = await api("/api/v1/capabilities/check", {
      method: "POST",
      body: form,
    });
    renderCapability(response.data);
    if (!options.silent) {
      showToast(response.data.ready ? "Capability ready." : "Capability blocked.");
    }
  } catch (error) {
    if (!options.silent) {
      showToast(error.message);
    }
  } finally {
    setBusy(nodes.checkCapabilityButton, false, "Check");
  }
}

function renderCapability(capability) {
  nodes.capabilityReady.textContent = capability.ready ? "Ready" : "Blocked";
  nodes.capabilityReady.className = `meta ${capability.ready ? "ready" : "blocked"}`;
  clear(nodes.capabilityPanel);
  nodes.capabilityPanel.className = "capability-grid";

  const checkGrid = document.createElement("div");
  checkGrid.className = "check-grid";
  Object.entries(capability.checks || {}).forEach(([key, value]) => {
    const row = document.createElement("div");
    row.className = "check-row";
    const label = document.createElement("strong");
    label.textContent = labelize(key);
    row.append(label);
    row.append(tag(value ? "Yes" : "No", value ? "ready" : "blocked"));
    checkGrid.append(row);
  });
  nodes.capabilityPanel.append(checkGrid);

  if (capability.blocked_reasons && capability.blocked_reasons.length) {
    nodes.capabilityPanel.append(listCard("Blocked reasons", capability.blocked_reasons));
  }
  if (capability.next_actions && capability.next_actions.length) {
    nodes.capabilityPanel.append(listCard("Next actions", capability.next_actions));
  }
}

async function generateSample() {
  setBusy(nodes.generateButton, true, "Generating");
  try {
    const payload = {
      app_name: nodes.testName.value.trim() || "Android App",
      package_name: nodes.packageName.value.trim() || null,
      goal: nodes.testGoal.value.trim() || null,
      platform: getSelectedPlatform(),
    };
    const response = await api("/api/v1/samples/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.sample = response.data;
    nodes.flowEditor.value = JSON.stringify(state.sample, null, 2);
    nodes.sampleStatus.textContent = "Ready for review";
    showToast("Sample generated.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.generateButton, false, "Generate sample");
  }
}

async function createRun(event) {
  event.preventDefault();
  const platform = getSelectedPlatform();
  if (platform === "ios") {
    await checkCapability();
    showToast("iOS execution is blocked until artifact, bundleId and signing inputs are ready.");
    return;
  }
  if (!nodes.apkFile.files[0]) {
    showToast("Select an APK before creating the run.");
    return;
  }

  const form = new FormData();
  form.append("apk", nodes.apkFile.files[0]);
  form.append("test_name", nodes.testName.value.trim() || "Android local MVP run");
  form.append("platform", platform);
  form.append("device_id", nodes.deviceSelect.value || "");
  form.append("package_name", nodes.packageName.value.trim());
  form.append("run_mode", getSelectedRunMode());

  const flow = readFlowPayload();
  if (flow === false) {
    return;
  }
  if (flow) {
    form.append("sample_mode", "provided");
    form.append("flow_json", JSON.stringify(flow));
  } else {
    form.append("sample_mode", "auto");
  }

  setBusy(nodes.createButton, true, "Creating");
  try {
    const response = await api("/api/v1/runs", {
      method: "POST",
      body: form,
    });
    if (!response.success) {
      renderCapability(response.data);
      showToast(response.error ? response.error.message : "Run was blocked.");
      return;
    }
    state.currentRun = response.data;
    localStorage.setItem("app-auto-test:last-run-id", state.currentRun.run_id);
    await loadRuns();
    await selectRun(state.currentRun.run_id);
    showToast("Run created.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.createButton, false, platform === "ios" ? "Check iOS capability" : "Create run");
  }
}

function readFlowPayload() {
  const raw = nodes.flowEditor.value.trim();
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    showToast("Generated sample JSON is invalid.");
    return false;
  }
}

async function selectRun(runId) {
  stopPolling();
  try {
    const response = await api(`/api/v1/runs/${encodeURIComponent(runId)}`);
    state.currentRun = response.data;
    localStorage.setItem("app-auto-test:last-run-id", runId);
    renderRunSummary(state.currentRun);
    renderRuns();
    await Promise.all([loadEvents(runId), loadReport(runId)]);
    if (["created", "queued", "running", "health_checked"].includes(state.currentRun.status)) {
      state.pollTimer = window.setInterval(() => selectRun(runId), 3000);
    }
  } catch (error) {
    showToast(error.message);
  }
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function renderRunSummary(run) {
  clear(nodes.runSummary);
  nodes.runSummary.className = "run-summary report-card";

  const title = document.createElement("div");
  title.className = "title-line";
  title.append(textSpan(run.test_name));
  title.append(tag(run.status, statusClass(run.status)));
  nodes.runSummary.append(title);

  const details = document.createElement("div");
  details.className = "details";
  details.textContent = [
    run.run_id,
    run.platform,
    run.run_mode,
    run.device_id || "no device",
    run.package_name || "no package",
  ].join(" | ");
  nodes.runSummary.append(details);

  if (run.blocked_reasons && run.blocked_reasons.length) {
    nodes.runSummary.append(listCard("Blocked reasons", run.blocked_reasons));
  }
  if (run.next_actions && run.next_actions.length) {
    nodes.runSummary.append(listCard("Next actions", run.next_actions));
  }
}

function renderRuns() {
  nodes.runCount.textContent = `${state.runs.length} run${state.runs.length === 1 ? "" : "s"}`;
  clear(nodes.runList);
  if (!state.runs.length) {
    nodes.runList.append(empty("No runs created yet."));
    return;
  }
  state.runs.slice(0, 8).forEach((run) => {
    const item = document.createElement("article");
    item.className = `run-item ${state.currentRun && state.currentRun.run_id === run.run_id ? "active" : ""}`;
    item.tabIndex = 0;
    item.addEventListener("click", () => selectRun(run.run_id));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRun(run.run_id);
      }
    });

    const body = document.createElement("div");
    const title = document.createElement("div");
    title.className = "title-line";
    title.append(textSpan(run.test_name));
    title.append(tag(run.status, statusClass(run.status)));
    body.append(title);

    const details = document.createElement("div");
    details.className = "details";
    details.textContent = `${run.run_id} | ${run.package_name || "no package"} | ${formatDate(run.created_at)}`;
    body.append(details);

    item.append(body);
    item.append(tag(run.report_status || "pending", statusClass(run.report_status)));
    nodes.runList.append(item);
  });
}

async function loadEvents(runId) {
  const response = await api(`/api/v1/runs/${encodeURIComponent(runId)}/events`);
  const events = response.data.items || [];
  nodes.eventCount.textContent = `${events.length} event${events.length === 1 ? "" : "s"}`;
  clear(nodes.eventList);
  if (!events.length) {
    nodes.eventList.append(empty("No events recorded."));
    return;
  }
  events.slice().reverse().forEach((event) => {
    const item = document.createElement("article");
    item.className = "event-item";
    const title = document.createElement("div");
    title.className = "title-line";
    const code = document.createElement("code");
    code.textContent = event.event_type;
    title.append(code);
    title.append(tag(event.status || "event", statusClass(event.status)));
    item.append(title);
    const details = document.createElement("div");
    details.className = "details";
    details.textContent = `${event.message} | ${formatDate(event.occurred_at)}`;
    item.append(details);
    nodes.eventList.append(item);
  });
}

async function loadReport(runId) {
  clear(nodes.reportView);
  nodes.exportHtmlButton.disabled = true;
  nodes.exportJsonButton.disabled = true;
  try {
    const response = await api(`/api/v1/runs/${encodeURIComponent(runId)}/report`);
    const payload = response.data;
    nodes.reportStatus.textContent = payload.report.status;
    nodes.reportStatus.className = `meta ${statusClass(payload.report.status)}`;
    renderReport(payload);
    nodes.exportHtmlButton.disabled = false;
    nodes.exportJsonButton.disabled = false;
  } catch (error) {
    nodes.reportStatus.textContent = "Pending";
    nodes.reportStatus.className = "meta";
    nodes.reportView.className = "report-view empty-state";
    nodes.reportView.textContent = "Report not generated.";
  }
}

function renderReport(payload) {
  nodes.reportView.className = "report-view report-card";
  const summary = document.createElement("div");
  summary.className = "title-line";
  summary.append(textSpan(payload.report.result_summary));
  summary.append(tag(payload.report.status, statusClass(payload.report.status)));
  nodes.reportView.append(summary);

  const runDetails = document.createElement("div");
  runDetails.className = "details";
  runDetails.textContent = `${payload.report.run_id} | generated ${formatDate(payload.generatedAt)}`;
  nodes.reportView.append(runDetails);

  if (payload.run.blocked_reasons && payload.run.blocked_reasons.length) {
    nodes.reportView.append(listCard("Blocked reasons", payload.run.blocked_reasons));
  }
  if (payload.report.next_actions && payload.report.next_actions.length) {
    nodes.reportView.append(listCard("Next actions", payload.report.next_actions));
  }
}

function exportReport(format) {
  if (!state.currentRun) {
    return;
  }
  const runId = encodeURIComponent(state.currentRun.run_id);
  window.location.assign(`/api/v1/runs/${runId}/report/export?format=${encodeURIComponent(format)}`);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof body === "string" ? body : body.detail || body.error?.message || "Request failed";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return body;
}

function getSelectedPlatform() {
  return document.querySelector("input[name='platform']:checked").value;
}

function getSelectedRunMode() {
  return document.querySelector("input[name='runMode']:checked").value;
}

function setBusy(button, busy, text) {
  button.disabled = busy;
  button.textContent = text;
}

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function empty(message) {
  const div = document.createElement("div");
  div.className = "empty-state";
  div.textContent = message;
  return div;
}

function tag(label, mode) {
  const span = document.createElement("span");
  span.className = `tag ${mode || ""}`.trim();
  span.textContent = label;
  return span;
}

function textSpan(value) {
  const span = document.createElement("span");
  span.textContent = value || "-";
  return span;
}

function listCard(title, items) {
  const card = document.createElement("div");
  card.className = "capability-card";
  const heading = document.createElement("h4");
  heading.textContent = title;
  card.append(heading);
  const list = document.createElement("ul");
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.append(li);
  });
  card.append(list);
  return card;
}

function statusClass(value) {
  if (!value) {
    return "";
  }
  if (["passed", "generated", "online", "ready"].includes(value)) {
    return "ready";
  }
  if (["blocked", "failed", "unavailable", "offline"].includes(value)) {
    return "blocked";
  }
  return "warning";
}

function labelize(value) {
  return value
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (first) => first.toUpperCase());
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function showToast(message) {
  nodes.toast.textContent = message;
  nodes.toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    nodes.toast.classList.remove("visible");
  }, 3600);
}
