const ACTION_LABELS = {
  launchApp: "启动应用",
  tapOn: "点击元素",
  inputText: "输入文本",
  assertVisible: "断言可见",
  scroll: "滚动",
  back: "返回",
  wait: "等待",
  takeScreenshot: "截图",
};

const TOOL_LABELS = {
  launchApp: "启动应用",
  tapOn: "点击元素",
  inputText: "输入文本",
  assertVisible: "断言可见",
  scroll: "滚动",
  back: "返回",
  wait: "等待",
  takeScreenshot: "截图",
  collectLogs: "采集日志",
  shell: "Shell 命令",
  network_request: "网络请求",
  read_secret: "读取密钥",
  write_file: "写文件",
  raw_device_control: "原始设备控制",
};

const STATUS_LABELS = {
  created: "已创建",
  health_checked: "已检查环境",
  queued: "排队中",
  running: "执行中",
  passed: "通过",
  failed: "失败",
  blocked: "已阻断",
  cancelled: "已取消",
  uploaded: "已上传",
  extracting: "抽取中",
  extract_failed: "抽取失败",
  privacy_scanning: "隐私扫描中",
  privacy_blocked: "隐私阻断",
  privacy_failed: "隐私扫描失败",
  parsed: "已解析",
  validation_failed: "校验失败",
  validated: "校验通过",
  confirmed: "已确认",
  rejected: "已退回",
  pending: "待生成",
  generated: "已生成",
  online: "在线",
  offline: "离线",
  unavailable: "不可用",
  ready: "就绪",
};

const PLATFORM_LABELS = {
  android: "Android",
  ios: "iOS",
};

const RUN_MODE_LABELS = {
  health_check: "仅检查环境",
  execute: "真实执行",
};

const DEVICE_KIND_LABELS = {
  emulator: "模拟器",
  physical: "真机",
  simulator: "模拟器",
  unknown: "未知",
};

const CHECK_LABELS = {
  adbAvailable: "ADB 可用",
  deviceSelected: "已选择设备",
  deviceOnline: "设备在线",
  apkUploaded: "已提供 APK",
  packageNameProvided: "已填写包名",
  maestroAvailable: "Maestro 可用",
  realExecutionEnabled: "真实执行开关",
  xcodeAvailable: "Xcode/xcrun 可用",
  simctlAvailable: "simctl 可用",
  simulatorAvailable: "iOS 模拟器可用",
  iosArtifactProvided: "已提供 IPA",
  bundleIdProvided: "已填写 bundleId",
  signingReady: "签名资料就绪",
  deviceAvailable: "iOS 目标设备可用",
  runnerConfigured: "Runner 路线已确认",
};

const REASON_LABELS = {
  ADB_NOT_FOUND: "未找到 ADB",
  ADB_COMMAND_FAILED: "ADB 命令执行失败",
  ANDROID_DEVICE_NOT_FOUND: "未发现 Android 设备",
  ANDROID_DEVICE_NOT_SELECTED: "未选择 Android 设备",
  ANDROID_DEVICE_NOT_ONLINE: "Android 设备不在线",
  APK_MISSING: "未上传 APK",
  PACKAGE_NAME_MISSING: "未填写包名",
  MAESTRO_NOT_FOUND: "未找到 Maestro",
  REAL_EXECUTION_DISABLED: "真实执行开关未开启",
  RUN_MODE_HEALTH_CHECK_ONLY: "当前为仅检查环境模式",
  APK_OR_PACKAGE_NAME_MISSING: "APK 或包名缺失",
  ADB_OR_DEVICE_NOT_RESOLVED: "ADB 或设备未解析成功",
  IOS_ARTIFACT_MISSING: "缺少 iOS IPA 产物",
  IOS_BUNDLE_ID_MISSING: "缺少 iOS bundleId",
  IOS_SIGNING_MISSING: "缺少 iOS 签名资料",
  IOS_DEVICE_MISSING: "缺少 iOS 目标设备",
  IOS_RUNNER_MISSING: "缺少 iOS Runner 路线",
  IOS_EXECUTION_BLOCKED: "iOS 真实执行已阻断",
  CASE_FILE_UNSUPPORTED_TYPE: "不支持的用例文件格式",
  CASE_FILE_LEGACY_DOC_UNSUPPORTED: "不支持 legacy .doc 文件",
  CASE_FILE_YAML_UNSUPPORTED: "不支持直接上传 YAML",
  CASE_FILE_TOO_LARGE: "用例文件超出大小限制",
  CASE_TEXT_TOO_LARGE: "抽取文本超出大小限制",
  CASE_FILE_EMPTY: "用例文件为空",
  CASE_FILE_DECODE_FAILED: "用例文本无法解码",
  CASE_FILE_DOCX_ENCRYPTED: "DOCX 无法读取或受保护",
  CASE_PRIVACY_BLOCKED: "用例文件命中隐私阻断",
  CASE_PRIVACY_SCAN_FAILED: "隐私扫描失败",
  CASE_DRAFT_VALIDATION_FAILED: "用例草稿校验失败",
  FLOW_CONFIRMATION_REQUIRED: "用例需要确认",
  FLOW_DRAFT_NOT_FOUND: "用例草稿不存在",
  FLOW_DRAFT_NOT_CONFIRMED: "用例草稿未确认",
  FLOW_DRAFT_HASH_MISMATCH: "用例草稿已变更，需要重新确认",
};

const NEXT_ACTION_LABELS = {
  "Set APP_AUTO_TEST_ADB_PATH or add adb to PATH.": "配置 APP_AUTO_TEST_ADB_PATH，或将 adb 加入 PATH。",
  "Select one online Android device or emulator in the tool.": "在控制台选择一台在线 Android 真机或模拟器。",
  "Start the selected emulator or reconnect the Android device.": "启动所选模拟器，或重新连接 Android 真机。",
  "Upload an APK when creating the test run.": "创建运行前上传 APK。",
  "Provide packageName or install aapt so it can be inferred.": "填写 packageName，或安装 aapt/aapt2 以便自动推断。",
  "Install Maestro or configure APP_AUTO_TEST_MAESTRO_BIN.": "安装 Maestro，或配置 APP_AUTO_TEST_MAESTRO_BIN。",
  "Set APP_AUTO_TEST_ALLOW_REAL_EXECUTION=true after reviewing runner permissions.": "确认 runner 权限后设置 APP_AUTO_TEST_ALLOW_REAL_EXECUTION=true。",
  "Create the run with runMode=execute after reviewing the generated flow.": "确认生成的用例后，将运行模式切换为真实执行。",
  "Upload APK and provide packageName.": "上传 APK 并填写 packageName。",
  "Select an online Android device and configure adb before execution.": "执行前选择在线 Android 设备并配置 adb。",
  "Provide IPA, bundleId, signing method and a target iOS device or simulator before real iOS execution.": "真实 iOS 执行前补齐 IPA、bundleId、签名方式和目标设备/模拟器。",
};

const PRIVACY_LABELS = {
  unscanned: "未扫描",
  clean: "无需脱敏",
  redacted: "已脱敏",
  blocked: "已阻断",
  failed: "扫描失败",
};

const PRIVACY_FINDING_LABELS = {
  email: "邮箱",
  phone: "手机号",
  id_card: "身份证号",
  authorization: "Authorization",
  api_key: "API Key",
  token: "Token",
  password: "密码",
  secret: "Secret",
  cookie: "Cookie",
  verification_code: "验证码",
  private_key: "私钥",
};

const EVENT_LABELS = {
  HEALTH_CHECKED: "环境检查完成",
  SAMPLE_READY: "用例已生成",
  RUN_BLOCKED: "运行已阻断",
  RUN_STARTED: "运行已开始",
  RUN_FINISHED: "运行已完成",
  RUN_FAILED: "运行失败",
  MAESTRO_FLOW_READY: "Maestro Flow 已准备",
  MAESTRO_STARTED: "Maestro 已启动",
  MAESTRO_FINISHED: "Maestro 已完成",
  MAESTRO_FAILED: "Maestro 执行失败",
};

const EVENT_MESSAGE_LABELS = {
  "Capability check completed.": "能力检查已完成。",
  "Auto sample flow is ready for review.": "自动样例用例已生成，等待确认。",
  "Run blocked before device execution.": "运行在进入设备执行前被阻断。",
  "Health-check mode does not execute the app.": "仅检查环境模式不会执行 App。",
  "Android local execution started.": "Android 本地执行已开始。",
  "Android local execution passed.": "Android 本地执行通过。",
  "Android local execution failed.": "Android 本地执行失败。",
  "APK or packageName is missing.": "APK 或包名缺失。",
  "Resolved adb command or deviceId is missing.": "ADB 命令或 deviceId 未解析成功。",
};

const FIELD_LABELS = {
  adb: "adb",
  deviceId: "deviceId",
  apk: "APK",
  packageName: "packageName",
  maestro: "Maestro",
  ipa: "IPA",
  bundleId: "bundleId",
  signingProfile: "签名配置",
  targetDevice: "目标设备",
  runnerType: "Runner 路线",
};

const IOS_READINESS_ITEMS = [
  {
    label: "IPA",
    field: "ipa",
    check: "iosArtifactProvided",
    reason: "IOS_ARTIFACT_MISSING",
    blockedText: "缺少可用于测试或重签的 IPA 产物。",
    nextAction: "补齐 IPA 或构建产物获取方式。",
  },
  {
    label: "bundleId",
    field: "bundleId",
    check: "bundleIdProvided",
    reason: "IOS_BUNDLE_ID_MISSING",
    blockedText: "缺少待测 App 的 bundleId。",
    nextAction: "确认 bundleId，并与 IPA 产物保持一致。",
  },
  {
    label: "签名配置",
    field: "signingProfile",
    check: "signingReady",
    reason: "IOS_SIGNING_MISSING",
    blockedText: "缺少签名方式、证书或描述文件责任路径。",
    nextAction: "补齐签名/重签方式、证书、描述文件和 UDID 覆盖口径。",
  },
  {
    label: "目标设备",
    field: "targetDevice",
    check: "deviceAvailable",
    reason: "IOS_DEVICE_MISSING",
    blockedText: "缺少可执行的 iOS 目标设备、模拟器或云真机来源。",
    nextAction: "确认设备来源、系统版本、并发和租约释放规则。",
  },
  {
    label: "Runner 路线",
    field: "runnerType",
    check: "runnerConfigured",
    reason: "IOS_RUNNER_MISSING",
    blockedText: "缺少 WDA、Appium、Maestro 或云真机重签执行路线。",
    nextAction: "确认 Runner 类型、宿主环境和失败证据采集方式。",
  },
];

const FALLBACK_MANIFEST = {
  allowed_tools: Object.keys(ACTION_LABELS),
  denied_tools: ["shell", "network_request", "read_secret", "write_file", "raw_device_control"],
  provider_boundary: "Only the local runner may call adb or Maestro; generated flows require review.",
  real_execution_enabled: false,
};

const DEFAULT_VERIFICATION_SCOPE = "打开应用并确认首页可见";

const state = {
  health: null,
  devices: [],
  runs: [],
  sample: null,
  currentRun: null,
  pollTimer: null,
  toolManifest: null,
  flowValidation: null,
  flowConfirmed: false,
  testcaseDraft: null,
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
    "deviceSelect",
    "generateButton",
    "createButton",
    "checkCapabilityButton",
    "toolManifestStatus",
    "toolBoundaryPanel",
    "agentPrompt",
    "copyPromptButton",
    "refreshManifestButton",
    "testcaseFile",
    "uploadTestcaseButton",
    "rejectTestcaseButton",
    "testcaseStatus",
    "testcasePanel",
    "flowEditor",
    "flowJsonStatus",
    "validateFlowButton",
    "confirmFlowButton",
    "validationPanel",
    "deviceCount",
    "deviceList",
    "capabilityReady",
    "capabilityPanel",
    "sampleStatus",
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
  nodes.packageName.addEventListener("input", () => {
    renderAgentPrompt();
    markFlowDirty();
  });
  nodes.testName.addEventListener("input", renderAgentPrompt);
  nodes.flowEditor.addEventListener("input", markFlowDirty);
  nodes.validateFlowButton.addEventListener("click", () => validateFlow());
  nodes.confirmFlowButton.addEventListener("click", confirmFlow);
  nodes.uploadTestcaseButton.addEventListener("click", uploadTestcaseFile);
  nodes.rejectTestcaseButton.addEventListener("click", rejectTestcaseDraft);
  nodes.testcaseFile.addEventListener("change", handleTestcaseFileChange);
  nodes.copyPromptButton.addEventListener("click", copyPrompt);
  nodes.refreshManifestButton.addEventListener("click", loadToolManifest);
  document.querySelectorAll("input[name='platform']").forEach((input) => {
    input.addEventListener("change", handlePlatformChange);
  });
  document.querySelectorAll("input[name='runMode']").forEach((input) => {
    input.addEventListener("change", renderAgentPrompt);
  });
  document.querySelectorAll("input[name='agentProvider']").forEach((input) => {
    input.addEventListener("change", renderAgentPrompt);
  });
}

async function refreshAll() {
  setBusy(nodes.refreshButton, true, "刷新中");
  try {
    await Promise.all([loadHealth(), loadDevices(), loadRuns(), loadToolManifest()]);
    await checkCapability({ silent: true });
    const savedRunId = localStorage.getItem("app-auto-test:last-run-id");
    const selectedRun = state.runs.find((run) => run.run_id === savedRunId) || state.runs[0];
    if (selectedRun) {
      await selectRun(selectedRun.run_id);
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.refreshButton, false, "刷新");
  }
}

async function loadHealth() {
  const response = await api("/api/v1/health");
  state.health = response.data;
  nodes.apiStatus.textContent = state.health.status === "ok" ? "API 在线" : "API 不可用";
  nodes.apiStatus.className = `status-pill ${state.health.status === "ok" ? "ready" : "blocked"}`;
  nodes.executionMode.textContent = state.health.realExecutionEnabled ? "真实执行已开启" : "真实执行已关闭";
  nodes.executionMode.className = `status-pill ${state.health.realExecutionEnabled ? "ready" : "warning"}`;
  if (state.toolManifest) {
    state.toolManifest.real_execution_enabled = state.health.realExecutionEnabled;
    renderToolManifest();
  }
}

async function loadToolManifest() {
  setBusy(nodes.refreshManifestButton, true, "刷新中");
  try {
    const response = await api("/api/v1/tools/manifest");
    state.toolManifest = response.data || FALLBACK_MANIFEST;
    nodes.toolManifestStatus.textContent = "工具边界已加载";
    nodes.toolManifestStatus.className = "meta ready";
  } catch (error) {
    state.toolManifest = { ...FALLBACK_MANIFEST };
    nodes.toolManifestStatus.textContent = "使用本地工具边界";
    nodes.toolManifestStatus.className = "meta warning";
  } finally {
    renderToolManifest();
    renderAgentPrompt();
    setBusy(nodes.refreshManifestButton, false, "刷新工具边界");
  }
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
    option.textContent = `${device.name}（${translateDeviceKind(device.kind)}，${translateStatus(device.status)}）`;
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
  nodes.deviceCount.textContent = `${state.devices.length} 个目标`;
  clear(nodes.deviceList);
  if (!state.devices.length) {
    nodes.deviceList.append(empty("未返回可选目标。"));
    return;
  }
  state.devices.forEach((device) => {
    const item = document.createElement("article");
    item.className = "device-item";

    const body = document.createElement("div");
    const title = document.createElement("div");
    title.className = "title-line";
    title.append(textSpan(device.name));
    title.append(tag(device.selectable ? "可选择" : "已阻断", device.selectable ? "ready" : "blocked"));
    body.append(title);

    const details = document.createElement("div");
    details.className = "details";
    details.textContent = [
      translatePlatform(device.platform),
      translateDeviceKind(device.kind),
      device.serial || device.id,
      translateReason(device.blocked_reason),
    ]
      .filter(Boolean)
      .join(" | ");
    body.append(details);

    item.append(body);
    item.append(tag(translateStatus(device.status), statusClass(device.status)));
    nodes.deviceList.append(item);
  });
}

function renderToolManifest() {
  const manifest = state.toolManifest || FALLBACK_MANIFEST;
  clear(nodes.toolBoundaryPanel);
  nodes.toolBoundaryPanel.className = "capability-grid";
  nodes.toolBoundaryPanel.append(
    listCard(
      "允许生成的受控动作",
      (manifest.allowed_tools || []).map(translateTool),
    ),
  );
  nodes.toolBoundaryPanel.append(
    listCard(
      "禁止 Agent 直接使用",
      (manifest.denied_tools || []).map(translateTool),
    ),
  );
  nodes.toolBoundaryPanel.append(
    infoCard("执行边界", [
      "Codex/Cursor 第一版只生成 SampleFlowDTO JSON。",
      "Maestro YAML 只能由后端根据受控 JSON 派生。",
      "Agent 不接 token、不调用外部 API、不直接执行 adb、maestro 或 shell。",
      manifest.real_execution_enabled ? "真实执行开关已开启。" : "真实执行开关默认关闭，缺条件时只生成 blocked 报告。",
    ]),
  );
}

function renderAgentPrompt() {
  if (!nodes.agentPrompt) {
    return;
  }
  const provider = getSelectedAgentProvider();
  const providerLabel = provider === "manual" ? "人工编写" : provider === "cursor" ? "Cursor Agent" : "Codex";
  const platform = getSelectedPlatform();
  const packageName = nodes.packageName.value.trim() || "com.example.app";
  const verificationScope = deriveVerificationScope();
  const allowedActions = Object.keys(ACTION_LABELS).join(", ");
  nodes.agentPrompt.value = [
    `你是 ${providerLabel}，请为 App 自动化测试生成一个 SampleFlowDTO JSON。`,
    "",
    "硬性约束：",
    "- 只输出一个 JSON 对象，不要输出 Markdown、注释、Maestro YAML 或 shell 命令。",
    "- action 只能使用以下白名单：" + allowedActions + "。",
    "- target、text、package_name 必须是单行字符串，不能包含换行、回车或 NUL。",
    "- 不要读取密钥、写文件、发网络请求、执行 adb/maestro/shell。",
    "- iOS 当前只允许生成阻断说明或检查思路，不声明真实执行可用。",
    "",
    "当前输入：",
    `- 平台：${translatePlatform(platform)}`,
    `- 包名：${packageName}`,
    `- 验证范围：${verificationScope}`,
    `- 运行模式：${translateRunMode(getSelectedRunMode())}`,
    "",
    "JSON 结构示例：",
    JSON.stringify(
      {
        name: "首页冒烟测试",
        platform,
        package_name: packageName,
        generated_from: provider,
        steps: [
          { action: "launchApp", target: packageName },
          { action: "wait", timeout_ms: 3000 },
          { action: "takeScreenshot", target: "home_loaded" },
          { action: "assertVisible", text: "Home" },
        ],
        requires_confirmation: true,
      },
      null,
      2,
    ),
  ].join("\n");
}

function deriveVerificationScope() {
  const currentFlowScope = deriveScopeFromFlow(readFlowPayloadForScope());
  if (currentFlowScope) {
    return currentFlowScope;
  }

  const draft = state.testcaseDraft || {};
  const draftFlowScope = deriveScopeFromFlow(draft.sample_flow);
  if (draftFlowScope) {
    return draftFlowScope;
  }

  const previewScope = firstMeaningfulLine(draft.redacted_preview);
  if (previewScope) {
    return previewScope;
  }

  const fragmentScope = firstMeaningfulLine((draft.unmapped_fragments || []).find(Boolean));
  if (fragmentScope) {
    return fragmentScope;
  }

  const draftFileScope = scopeFromFileName(draft.asset && draft.asset.file_name);
  if (draftFileScope) {
    return draftFileScope;
  }

  const selectedFileScope = scopeFromFileName(nodes.testcaseFile?.files?.[0]?.name);
  return selectedFileScope || DEFAULT_VERIFICATION_SCOPE;
}

function readFlowPayloadForScope() {
  const raw = nodes.flowEditor && typeof nodes.flowEditor.value === "string" ? nodes.flowEditor.value.trim() : "";
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_error) {
    return null;
  }
}

function deriveScopeFromFlow(flow) {
  if (!isPlainObject(flow)) {
    return "";
  }
  const name = normalizeScopeText(flow.name);
  if (name) {
    return name;
  }
  const steps = Array.isArray(flow.steps) ? flow.steps : [];
  return steps.map(scopeFromSpecificStep).find(Boolean) || steps.map(scopeFromStep).find(Boolean) || "";
}

function scopeFromSpecificStep(step) {
  if (!isPlainObject(step)) {
    return "";
  }
  const value = normalizeScopeText(step.text || step.target || step.note);
  if (step.action === "assertVisible" && value) {
    return `确认${value}可见`;
  }
  if (step.action === "tapOn" && value) {
    return `点击${value}`;
  }
  if (step.action === "inputText" && value) {
    return `输入${value}`;
  }
  if (step.action === "takeScreenshot") {
    return value ? `采集${value}截图` : "采集截图";
  }
  if (step.action === "scroll") {
    return "滑动页面";
  }
  if (step.action === "back") {
    return "返回上一页";
  }
  return "";
}

function scopeFromStep(step) {
  if (!isPlainObject(step)) {
    return "";
  }
  if (step.action === "launchApp") {
    return "打开应用";
  }
  return scopeFromSpecificStep(step);
}

function firstMeaningfulLine(value) {
  if (Array.isArray(value)) {
    return value.map(firstMeaningfulLine).find(Boolean) || "";
  }
  return String(value || "")
    .split(/\r?\n/)
    .map(normalizeScopeText)
    .find(Boolean) || "";
}

function normalizeScopeText(value) {
  if (typeof value !== "string") {
    return "";
  }
  return value
    .replace(/[\r\n\x00]+/g, " ")
    .replace(/^\s*(?:[-*]|\d+[.)]|步骤\s*\d+[:：]?)\s*/, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 100);
}

function scopeFromFileName(fileName) {
  const normalized = normalizeScopeText(fileName);
  if (!normalized) {
    return "";
  }
  const withoutExtension = normalized.replace(/\.[^.]+$/, "");
  return withoutExtension.replace(/[_-]+/g, " ").trim();
}

async function handlePlatformChange() {
  const platform = getSelectedPlatform();
  nodes.createButton.textContent = platform === "ios" ? "查看 iOS 阻断" : "创建运行";
  nodes.apkFile.disabled = platform === "ios";
  nodes.apkFile.closest(".field").classList.toggle("disabled-field", platform === "ios");
  renderAgentPrompt();
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

  setBusy(nodes.checkCapabilityButton, true, "检查中");
  try {
    const response = await api("/api/v1/capabilities/check", {
      method: "POST",
      body: form,
    });
    renderCapability(response.data);
    if (!options.silent) {
      showToast(response.data.ready ? "能力检查通过。" : "能力检查已阻断，请查看原因和下一步。");
    }
  } catch (error) {
    if (!options.silent) {
      showToast(error.message);
    }
  } finally {
    setBusy(nodes.checkCapabilityButton, false, "检查能力");
  }
}

function renderCapability(capability) {
  nodes.capabilityReady.textContent = capability.ready ? "就绪" : "已阻断";
  nodes.capabilityReady.className = `meta ${capability.ready ? "ready" : "blocked"}`;
  clear(nodes.capabilityPanel);
  nodes.capabilityPanel.className = "capability-grid";

  const checkGrid = document.createElement("div");
  checkGrid.className = "check-grid";
  Object.entries(capability.checks || {}).forEach(([key, value]) => {
    const row = document.createElement("div");
    row.className = "check-row";
    const label = document.createElement("strong");
    label.textContent = CHECK_LABELS[key] || labelize(key);
    row.append(label);
    row.append(tag(value ? "是" : "否", value ? "ready" : "blocked"));
    checkGrid.append(row);
  });
  nodes.capabilityPanel.append(checkGrid);

  if (capability.missing_fields && capability.missing_fields.length) {
    nodes.capabilityPanel.append(listCard("缺失字段", capability.missing_fields.map(translateField)));
  }
  if (capability.blocked_reasons && capability.blocked_reasons.length) {
    nodes.capabilityPanel.append(listCard("阻断原因", capability.blocked_reasons.map(translateReason)));
  }
  if (capability.next_actions && capability.next_actions.length) {
    nodes.capabilityPanel.append(listCard("下一步", capability.next_actions.map(translateNextAction)));
  }
  const iosReadinessCard = renderIosReadinessChecklist(capability);
  if (iosReadinessCard) {
    nodes.capabilityPanel.append(iosReadinessCard);
  }
  if (capability.platform === "ios") {
    nodes.capabilityPanel.append(
      infoCard("iOS 签名阻断说明", [
        "当前只展示 capability 与 blocked 文案，不启动真实 iOS runner。",
        "需要 IPA、bundleId、签名方式、证书/描述文件、UDID 覆盖和目标设备后才能进入真实执行。",
        "本阶段不会生成真实通过/失败结论，只能生成阻断报告。",
      ]),
    );
  }
}

function handleTestcaseFileChange() {
  state.testcaseDraft = null;
  state.flowConfirmed = false;
  renderTestcaseDraft();
  renderValidation();
  renderAgentPrompt();
}

async function uploadTestcaseFile() {
  const file = nodes.testcaseFile.files[0];
  if (!file) {
    showToast("请选择 txt、md 或 docx 测试用例文件。");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("platform", getSelectedPlatform());
  form.append("package_name", nodes.packageName.value.trim());

  setBusy(nodes.uploadTestcaseButton, true, "上传中");
  nodes.testcaseStatus.textContent = "上传中";
  nodes.testcaseStatus.className = "meta warning";
  try {
    const response = await api("/api/v1/testcase-files", {
      method: "POST",
      body: form,
    });
    if (!response.success) {
      state.testcaseDraft = null;
      renderTestcaseDraft(response.error);
      showToast(translateReason(response.error?.code) || response.error?.message || "用例文件上传失败。");
      return;
    }
    applyTestcaseDraft(response.data);
    showToast("测试用例文件已生成草稿，请预览并确认。");
  } catch (error) {
    state.testcaseDraft = null;
    renderTestcaseDraft(error);
    showToast(translateReason(error.code) || error.message || "用例文件上传失败。");
  } finally {
    setBusy(nodes.uploadTestcaseButton, false, "上传解析");
  }
}

async function rejectTestcaseDraft() {
  if (!state.testcaseDraft || !state.testcaseDraft.draft_id) {
    state.testcaseDraft = null;
    state.flowConfirmed = false;
    renderTestcaseDraft();
    renderValidation();
    return;
  }
  setBusy(nodes.rejectTestcaseButton, true, "退回中");
  try {
    const response = await api(`/api/v1/testcase-files/${encodeURIComponent(state.testcaseDraft.draft_id)}/reject`, {
      method: "POST",
    });
    applyTestcaseDraft(response.data, { keepEditor: true });
    state.flowConfirmed = false;
    showToast("用例草稿已退回，可重新上传。");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.rejectTestcaseButton, false, "退回草稿");
  }
}

function applyTestcaseDraft(draft, options = {}) {
  state.testcaseDraft = normalizeTestcaseDraft(draft);
  state.flowConfirmed = state.testcaseDraft.flow_review_status === "confirmed";
  state.flowValidation = state.testcaseDraft.validation ? normalizeValidationResponse(state.testcaseDraft.validation) : null;
  if (state.flowValidation) {
    state.flowValidation.source = "server";
  }
  if (state.testcaseDraft.sample_flow && !options.keepEditor) {
    nodes.flowEditor.value = JSON.stringify(state.testcaseDraft.sample_flow, null, 2);
  } else if (!state.testcaseDraft.sample_flow && !options.keepEditor) {
    nodes.flowEditor.value = "";
  }
  nodes.sampleStatus.textContent = state.testcaseDraft.flow_review_status === "confirmed" ? "文件用例已确认" : "文件用例待确认";
  renderTestcaseDraft();
  renderValidation();
  renderAgentPrompt();
}

function normalizeTestcaseDraft(draft) {
  const safeDraft = draft || {};
  return {
    ...safeDraft,
    privacy_findings: (safeDraft.privacy_findings || []).map((finding) => ({
      kind: finding.kind || finding.type || "unknown",
      type: finding.type || finding.kind || "unknown",
      count: Number(finding.count || 0),
      severity: finding.severity || "warning",
    })),
    warnings: safeDraft.warnings || [],
    unmapped_fragments: safeDraft.unmapped_fragments || [],
  };
}

function renderTestcaseDraft(error) {
  if (!nodes.testcasePanel) {
    return;
  }
  clear(nodes.testcasePanel);
  const selectedFile = nodes.testcaseFile.files[0];
  if (error) {
    nodes.testcaseStatus.textContent = "上传失败";
    nodes.testcaseStatus.className = "meta blocked";
    nodes.testcasePanel.className = "empty-state";
    nodes.testcasePanel.textContent = `${translateReason(error.code) || "上传失败"}：${error.message || "请检查文件后重试。"}`;
    return;
  }
  if (!state.testcaseDraft) {
    nodes.testcaseStatus.textContent = selectedFile ? selectedFile.name : "未上传";
    nodes.testcaseStatus.className = "meta";
    nodes.testcasePanel.className = "empty-state";
    nodes.testcasePanel.textContent = "支持 txt、md、docx 测试用例文件。解析后只展示脱敏预览、命中类型和数量。";
    return;
  }

  const draft = state.testcaseDraft;
  nodes.testcaseStatus.textContent = translateStatus(draft.status);
  nodes.testcaseStatus.className = `meta ${statusClass(draft.status)}`;
  nodes.testcasePanel.className = "validation-panel";

  const title = document.createElement("div");
  title.className = "title-line";
  title.append(textSpan(draft.asset?.file_name || draft.draft_id));
  title.append(tag(translateStatus(draft.status), statusClass(draft.status)));
  title.append(tag(translatePrivacyStatus(draft.privacy_status), privacyStatusClass(draft.privacy_status)));
  nodes.testcasePanel.append(title);

  const detail = document.createElement("div");
  detail.className = "details";
  detail.textContent = [draft.draft_id, draft.asset ? `${Math.ceil(draft.asset.size_bytes / 1024)} KB` : "", draft.package_name || ""]
    .filter(Boolean)
    .join(" | ");
  nodes.testcasePanel.append(detail);

  if (draft.redacted_preview) {
    const preview = document.createElement("pre");
    preview.className = "preview-block";
    preview.textContent = draft.redacted_preview;
    nodes.testcasePanel.append(preview);
  }
  if (draft.privacy_findings.length) {
    nodes.testcasePanel.append(
      listCard(
        "隐私命中",
        draft.privacy_findings.map((finding) => `${translatePrivacyFinding(finding.kind)}：${finding.count} 处`),
      ),
    );
  }
  if (draft.warnings.length) {
    nodes.testcasePanel.append(listCard("提示", draft.warnings));
  }
  if (draft.unmapped_fragments.length) {
    nodes.testcasePanel.append(listCard("未映射片段", draft.unmapped_fragments));
  }
}

async function generateSample() {
  setBusy(nodes.generateButton, true, "生成中");
  try {
    const payload = {
      app_name: nodes.testName.value.trim() || "Android App",
      package_name: nodes.packageName.value.trim() || null,
      goal: deriveVerificationScope(),
      platform: getSelectedPlatform(),
    };
    const response = await api("/api/v1/samples/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.sample = response.data;
    state.testcaseDraft = null;
    state.flowValidation = null;
    state.flowConfirmed = false;
    nodes.flowEditor.value = JSON.stringify(state.sample, null, 2);
    nodes.sampleStatus.textContent = "样例已生成";
    nodes.flowJsonStatus.textContent = "待校验";
    renderAgentPrompt();
    renderTestcaseDraft();
    renderValidation();
    showToast("SampleFlowDTO 样例已生成，请校验并确认。");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.generateButton, false, "生成样例 JSON");
  }
}

async function validateFlow(options = {}) {
  const flow = readFlowPayload({ quiet: options.quiet });
  if (flow === false) {
    return null;
  }
  if (!flow) {
    const result = {
      valid: false,
      errors: ["请先生成或粘贴 SampleFlowDTO JSON。"],
      warnings: [],
      summary: "没有可校验的 JSON。",
      source: "client",
    };
    state.flowValidation = result;
    state.flowConfirmed = false;
    renderValidation();
    return result;
  }

  setBusy(nodes.validateFlowButton, true, "校验中");
  try {
    let result;
    try {
      const response = await api("/api/v1/flows/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildFlowValidationRequest(flow)),
      });
      result = normalizeValidationResponse(response.data);
      result.source = "server";
    } catch (error) {
      if (![404, 405].includes(error.status)) {
        throw error;
      }
      result = localValidateFlow(flow);
      result.source = "client";
    }

    state.flowValidation = result;
    state.flowConfirmed = false;
    renderValidation();
    if (!options.quiet) {
      showToast(result.valid ? "JSON 校验通过，请确认用例。" : "JSON 校验未通过，请查看错误。");
    }
    return result;
  } catch (error) {
    if (!options.quiet) {
      showToast(error.message);
    }
    return null;
  } finally {
    setBusy(nodes.validateFlowButton, false, "校验 JSON");
  }
}

async function confirmFlow() {
  const flow = readFlowPayload({ quiet: true });
  if (flow === false || !flow) {
    showToast("请先生成、上传或粘贴 SampleFlowDTO JSON。");
    return;
  }
  const result = state.flowValidation && state.flowValidation.valid ? state.flowValidation : await validateFlow({ quiet: true });
  if (!result || !result.valid) {
    showToast("校验通过后才能确认用例。");
    return;
  }
  if (state.testcaseDraft && state.testcaseDraft.draft_id) {
    setBusy(nodes.confirmFlowButton, true, "确认中");
    try {
      const response = await api(`/api/v1/testcase-files/${encodeURIComponent(state.testcaseDraft.draft_id)}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildFlowValidationRequest(flow)),
      });
      applyTestcaseDraft(response.data, { keepEditor: true });
      if (!response.success || state.testcaseDraft.flow_review_status !== "confirmed") {
        showToast(response.error ? translateReason(response.error.code) || response.error.message : "用例草稿未确认，请检查错误。");
        return;
      }
      showToast("用例草稿已由后端确认，创建运行会提交 draft id。");
      return;
    } catch (error) {
      showToast(error.message);
      return;
    } finally {
      setBusy(nodes.confirmFlowButton, false, "确认用例");
    }
  }
  state.flowConfirmed = true;
  renderValidation();
  showToast("用例已确认，创建运行时会提交该 JSON。");
}

function buildFlowValidationRequest(flow) {
  return {
    flow,
    platform: getSelectedPlatform(),
    package_name: nodes.packageName.value.trim() || null,
  };
}

function localValidateFlow(flow) {
  const errors = [];
  const warnings = [];
  const allowedActions = new Set(Object.keys(ACTION_LABELS));
  const platform = getSelectedPlatform();
  const packageName = nodes.packageName.value.trim();

  if (!isPlainObject(flow)) {
    return {
      valid: false,
      errors: ["顶层必须是 JSON 对象。"],
      warnings,
      summary: "本地校验发现错误。",
      source: "client",
    };
  }
  if (!flow.name || typeof flow.name !== "string") {
    errors.push("name 必须是非空字符串。");
  }
  if (!flow.package_name || typeof flow.package_name !== "string") {
    errors.push("package_name 必须是非空字符串。");
  } else if (!isSingleLine(flow.package_name)) {
    errors.push("package_name 不能包含换行、回车或 NUL。");
  } else if (packageName && flow.package_name !== packageName) {
    warnings.push("JSON 内 package_name 与左侧包名不一致，后端会以提交表单为准。");
  }
  if (flow.platform && flow.platform !== platform) {
    warnings.push(`JSON 平台为 ${translatePlatform(flow.platform)}，当前表单平台为 ${translatePlatform(platform)}。`);
  }
  if (!Array.isArray(flow.steps) || !flow.steps.length) {
    errors.push("steps 必须是非空数组。");
  } else {
    flow.steps.forEach((step, index) => {
      const label = `第 ${index + 1} 步`;
      if (!isPlainObject(step)) {
        errors.push(`${label} 必须是对象。`);
        return;
      }
      if (!allowedActions.has(step.action)) {
        errors.push(`${label} action 不在白名单内：${step.action || "空"}`);
      }
      ["target", "text", "note"].forEach((field) => {
        if (step[field] != null && (typeof step[field] !== "string" || !isSingleLine(step[field]))) {
          errors.push(`${label} ${field} 必须是单行字符串。`);
        }
      });
      if (step.timeout_ms != null && (!Number.isFinite(Number(step.timeout_ms)) || Number(step.timeout_ms) < 0)) {
        errors.push(`${label} timeout_ms 必须是非负数字。`);
      }
      if (["tapOn", "assertVisible"].includes(step.action) && !step.target && !step.text) {
        warnings.push(`${label} 建议填写 target 或 text，便于 Maestro 定位。`);
      }
      if (step.action === "inputText" && !step.text) {
        warnings.push(`${label} inputText 建议填写 text。`);
      }
    });
  }

  if (platform === "ios") {
    warnings.push("iOS 当前只做 capability blocked 展示，不会启动真实 runner。");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    summary: errors.length ? "本地校验发现错误。" : "本地校验通过，等待人工确认。",
    source: "client",
  };
}

function normalizeValidationResponse(data) {
  if (!data) {
    return null;
  }
  return {
    valid: Boolean(data.valid ?? data.ready ?? true),
    errors: normalizeMessages(data.errors || data.flow_validation_errors || []),
    warnings: normalizeMessages(data.warnings || []),
    summary: data.summary || data.message || "后端校验完成。",
  };
}

function normalizeMessages(items) {
  return (items || []).map((item) => {
    if (typeof item === "string") {
      return item;
    }
    if (item && typeof item === "object") {
      return [item.code, item.field, item.message].filter(Boolean).join(" | ");
    }
    return String(item);
  });
}

function renderValidation() {
  clear(nodes.validationPanel);
  nodes.validationPanel.className = "validation-panel";
  const result = state.flowValidation;
  if (!result) {
    nodes.validationPanel.className = "empty-state";
    nodes.validationPanel.textContent =
      state.testcaseDraft && state.testcaseDraft.privacy_status === "blocked"
        ? "测试用例文件命中阻断级隐私内容，不能确认或创建运行。"
        : "只接受 SampleFlowDTO JSON，不接受直接 Maestro YAML。校验通过并确认后才能作为用例提交。";
    nodes.confirmFlowButton.disabled = true;
    nodes.flowJsonStatus.textContent = nodes.flowEditor.value.trim() ? "待校验" : "待生成或导入";
    nodes.flowJsonStatus.className = "meta";
    return;
  }

  const heading = document.createElement("div");
  heading.className = "title-line";
  heading.append(textSpan(result.valid ? "JSON 校验通过" : "JSON 校验未通过"));
  heading.append(tag(result.source === "server" ? "后端校验" : "本地校验", result.valid ? "ready" : "warning"));
  nodes.validationPanel.append(heading);

  const detail = document.createElement("div");
  detail.className = "details";
  detail.textContent = result.summary;
  nodes.validationPanel.append(detail);

  if (result.errors.length) {
    nodes.validationPanel.append(listCard("错误", result.errors));
  }
  if (result.warnings.length) {
    nodes.validationPanel.append(listCard("提示", result.warnings));
  }
  nodes.confirmFlowButton.disabled = !result.valid || (state.testcaseDraft && state.testcaseDraft.privacy_status === "blocked");
  nodes.flowJsonStatus.textContent = state.flowConfirmed ? "已确认" : result.valid ? "校验通过，待确认" : "校验未通过";
  nodes.flowJsonStatus.className = `meta ${state.flowConfirmed ? "ready" : result.valid ? "warning" : "blocked"}`;
}

function markFlowDirty() {
  state.flowValidation = null;
  state.flowConfirmed = false;
  if (state.testcaseDraft && state.testcaseDraft.flow_review_status === "confirmed") {
    state.testcaseDraft = {
      ...state.testcaseDraft,
      status: "validated",
      flow_review_status: "draft",
      confirmed_flow_hash: null,
    };
    renderTestcaseDraft();
  }
  renderValidation();
  renderAgentPrompt();
}

async function createRun(event) {
  event.preventDefault();
  const platform = getSelectedPlatform();
  if (platform === "ios") {
    await checkCapability();
    showToast("iOS 当前缺少 IPA、bundleId 和签名资料，只展示 blocked，不启动真实执行。");
    return;
  }
  if (!nodes.apkFile.files[0]) {
    showToast("创建运行前请先选择 APK。");
    return;
  }

  const form = new FormData();
  form.append("apk", nodes.apkFile.files[0]);
  form.append("test_name", nodes.testName.value.trim() || "Android 本地 MVP 运行");
  form.append("platform", platform);
  form.append("device_id", nodes.deviceSelect.value || "");
  form.append("package_name", nodes.packageName.value.trim());
  form.append("run_mode", getSelectedRunMode());

  const flow = readFlowPayload();
  if (flow === false) {
    return;
  }
  if (flow) {
    if (state.testcaseDraft && state.testcaseDraft.privacy_status === "blocked") {
      showToast("测试用例文件命中隐私阻断，不能创建运行。");
      return;
    }
    if (!state.flowConfirmed) {
      const result = await validateFlow({ quiet: true });
      if (!result || !result.valid) {
        showToast("SampleFlowDTO JSON 校验未通过。");
        return;
      }
      showToast("JSON 已校验通过，请点击“确认用例”后再创建运行。");
      return;
    }
    form.append("sample_mode", "provided");
    form.append("flow_json", JSON.stringify(flow));
    form.append("flow_review_status", "confirmed");
    if (state.testcaseDraft && state.testcaseDraft.draft_id) {
      if (state.testcaseDraft.flow_review_status !== "confirmed" || !state.testcaseDraft.confirmed_flow_hash) {
        showToast("用例草稿已变更，请重新确认后再创建运行。");
        return;
      }
      form.append("flow_draft_id", state.testcaseDraft.draft_id);
    }
  } else {
    form.append("sample_mode", "auto");
  }

  setBusy(nodes.createButton, true, "创建中");
  try {
    const response = await api("/api/v1/runs", {
      method: "POST",
      body: form,
    });
    if (!response.success) {
      renderCapability(response.data);
      showToast(response.error ? translateReason(response.error.code) || response.error.message : "运行已被阻断。");
      return;
    }
    state.currentRun = response.data;
    localStorage.setItem("app-auto-test:last-run-id", state.currentRun.run_id);
    await loadRuns();
    await selectRun(state.currentRun.run_id);
    showToast("运行已创建。");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(nodes.createButton, false, platform === "ios" ? "查看 iOS 阻断" : "创建运行");
  }
}

function readFlowPayload(options = {}) {
  const raw = nodes.flowEditor.value.trim();
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    if (!options.quiet) {
      const looksLikeYaml = raw.startsWith("appId:") || raw.includes("\n---") || raw.includes("- launchApp");
      showToast(looksLikeYaml ? "只接受 SampleFlowDTO JSON，不接受 Maestro YAML。" : "SampleFlowDTO JSON 格式无效。");
    }
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
  title.append(tag(translateStatus(run.status), statusClass(run.status)));
  nodes.runSummary.append(title);

  const details = document.createElement("div");
  details.className = "details";
  details.textContent = [
    run.run_id,
    translatePlatform(run.platform),
    translateRunMode(run.run_mode),
    run.device_id || "未选择设备",
    run.package_name || "未填写包名",
  ].join(" | ");
  nodes.runSummary.append(details);

  if (run.blocked_reasons && run.blocked_reasons.length) {
    nodes.runSummary.append(listCard("阻断原因", run.blocked_reasons.map(translateReason)));
  }
  if (run.next_actions && run.next_actions.length) {
    nodes.runSummary.append(listCard("下一步", run.next_actions.map(translateNextAction)));
  }
}

function renderRuns() {
  nodes.runCount.textContent = `${state.runs.length} 条运行`;
  clear(nodes.runList);
  if (!state.runs.length) {
    nodes.runList.append(empty("尚未创建运行。"));
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
    title.append(tag(translateStatus(run.status), statusClass(run.status)));
    body.append(title);

    const details = document.createElement("div");
    details.className = "details";
    details.textContent = `${run.run_id} | ${run.package_name || "未填写包名"} | ${formatDate(run.created_at)}`;
    body.append(details);

    item.append(body);
    item.append(tag(translateStatus(run.report_status || "pending"), statusClass(run.report_status)));
    nodes.runList.append(item);
  });
}

async function loadEvents(runId) {
  const response = await api(`/api/v1/runs/${encodeURIComponent(runId)}/events`);
  const events = response.data.items || [];
  nodes.eventCount.textContent = `${events.length} 条事件`;
  clear(nodes.eventList);
  if (!events.length) {
    nodes.eventList.append(empty("暂无事件记录。"));
    return;
  }
  events.slice().reverse().forEach((event) => {
    const item = document.createElement("article");
    item.className = "event-item";
    const title = document.createElement("div");
    title.className = "title-line";
    const code = document.createElement("code");
    code.textContent = EVENT_LABELS[event.event_type] || event.event_type;
    title.append(code);
    title.append(tag(translateStatus(event.status || "event"), statusClass(event.status)));
    item.append(title);
    const details = document.createElement("div");
    details.className = "details";
    details.textContent = `${translateEventMessage(event.message)} | ${formatDate(event.occurred_at)}`;
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
    nodes.reportStatus.textContent = translateStatus(payload.report.status);
    nodes.reportStatus.className = `meta ${statusClass(payload.report.status)}`;
    renderReport(payload);
    nodes.exportHtmlButton.disabled = false;
    nodes.exportJsonButton.disabled = false;
  } catch (error) {
    nodes.reportStatus.textContent = "待生成";
    nodes.reportStatus.className = "meta";
    nodes.reportView.className = "report-view empty-state";
    nodes.reportView.textContent = "报告尚未生成。";
  }
}

function renderReport(payload) {
  nodes.reportView.className = "report-view report-card";
  const summary = document.createElement("div");
  summary.className = "title-line";
  summary.append(textSpan(translateSummary(payload.report.result_summary)));
  summary.append(tag(translateStatus(payload.report.status), statusClass(payload.report.status)));
  nodes.reportView.append(summary);

  const runDetails = document.createElement("div");
  runDetails.className = "details";
  runDetails.textContent = `${payload.report.run_id} | 生成时间 ${formatDate(payload.generatedAt)}`;
  nodes.reportView.append(runDetails);

  if (payload.run.blocked_reasons && payload.run.blocked_reasons.length) {
    nodes.reportView.append(listCard("阻断原因", payload.run.blocked_reasons.map(translateReason)));
  }
  if (payload.report.next_actions && payload.report.next_actions.length) {
    nodes.reportView.append(listCard("下一步", payload.report.next_actions.map(translateNextAction)));
  }
  const iosReadinessCard = renderIosReadinessChecklist(findIosReadiness(payload));
  if (iosReadinessCard) {
    nodes.reportView.append(iosReadinessCard);
  }
}

function exportReport(format) {
  if (!state.currentRun) {
    return;
  }
  const runId = encodeURIComponent(state.currentRun.run_id);
  window.location.assign(`/api/v1/runs/${runId}/report/export?format=${encodeURIComponent(format)}`);
}

async function copyPrompt() {
  const value = nodes.agentPrompt.value;
  try {
    await navigator.clipboard.writeText(value);
    showToast("提示词已复制。");
  } catch (error) {
    nodes.agentPrompt.select();
    document.execCommand("copy");
    showToast("提示词已复制。");
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === "string" ? body : body.detail;
    const detailObject = isPlainObject(detail) ? detail : {};
    const code = detailObject.code || body.error?.code || (typeof detail === "string" && /^[A-Z0-9_]+$/.test(detail) ? detail : undefined);
    const message =
      detailObject.message ||
      body.error?.message ||
      (typeof detail === "string" ? detail : undefined) ||
      "请求失败";
    const error = new Error(message);
    error.status = response.status;
    error.code = code;
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

function getSelectedAgentProvider() {
  return document.querySelector("input[name='agentProvider']:checked").value;
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

function infoCard(title, lines) {
  return listCard(title, lines);
}

function renderIosReadinessChecklist(source) {
  const readiness = normalizeIosReadiness(source);
  if (!readiness) {
    return null;
  }
  const items = IOS_READINESS_ITEMS.map((item) => {
    const hasCheck = Object.prototype.hasOwnProperty.call(readiness.checks, item.check);
    const fieldMissing = readiness.missingFields.includes(item.field);
    const reasonHit = readiness.blockedReasons.includes(item.reason);
    const ready = hasCheck ? Boolean(readiness.checks[item.check]) : Boolean(readiness.ready && !fieldMissing && !reasonHit);
    return {
      ...item,
      ready,
      reasonHit,
      fieldMissing,
    };
  });

  const blockedCount = items.filter((item) => !item.ready).length;
  const card = document.createElement("div");
  card.className = "capability-card readiness-card";

  const heading = document.createElement("div");
  heading.className = "title-line";
  heading.append(textSpan("iOS readiness blocked 清单"));
  heading.append(tag(blockedCount ? `${blockedCount} 项阻断` : "就绪", blockedCount ? "blocked" : "ready"));
  card.append(heading);

  const guard = document.createElement("div");
  guard.className = "details";
  guard.textContent = "不得启动真实 iOS runner；这里只展示前置资料、签名、设备和 Runner 路线是否满足。";
  card.append(guard);

  const list = document.createElement("div");
  list.className = "readiness-list";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = `readiness-row ${item.ready ? "ready" : "blocked"}`;

    const title = document.createElement("div");
    title.className = "title-line";
    title.append(textSpan(item.label));
    title.append(tag(item.ready ? "已满足" : "已阻断", item.ready ? "ready" : "blocked"));
    row.append(title);

    const detail = document.createElement("div");
    detail.className = "details";
    if (item.ready) {
      detail.textContent = "当前 readiness 信号已满足。";
    } else {
      const parts = [item.blockedText];
      if (item.fieldMissing) {
        parts.push(`缺失字段：${translateField(item.field)}`);
      }
      if (item.reasonHit) {
        parts.push(`阻断原因：${translateReason(item.reason)}`);
      }
      parts.push(`下一步：${item.nextAction}`);
      detail.textContent = parts.join(" ");
    }
    row.append(detail);
    list.append(row);
  });
  card.append(list);
  return card;
}

function findIosReadiness(payload) {
  if (!payload) {
    return null;
  }
  const directSources = [
    payload.readiness,
    payload.ios_readiness,
    payload.iosReadiness,
    payload.capability,
    payload.run && payload.run.readiness,
    payload.run && payload.run.ios_readiness,
    payload.run && payload.run.iosReadiness,
    payload.run && payload.run.capability,
  ];
  for (const source of directSources) {
    const readiness = normalizeIosReadiness(source, payload.run && payload.run.platform);
    if (readiness) {
      return readiness;
    }
  }

  for (const event of payload.events || []) {
    const details = event.details || {};
    const eventSources = [details.capability, details.readiness, details.ios_readiness, details.iosReadiness, details];
    for (const source of eventSources) {
      const readiness = normalizeIosReadiness(source, payload.run && payload.run.platform);
      if (readiness) {
        return readiness;
      }
    }
  }

  if (payload.run && payload.run.platform === "ios") {
    return normalizeIosReadiness(
      {
        platform: "ios",
        ready: false,
        checks: {},
        missing_fields: payload.run.missing_fields || payload.run.missingFields || [],
        blocked_reasons: payload.run.blocked_reasons || payload.run.blockedReasons || [],
        next_actions: payload.run.next_actions || payload.run.nextActions || [],
      },
      "ios",
    );
  }
  return null;
}

function normalizeIosReadiness(source, fallbackPlatform) {
  if (!source || typeof source !== "object") {
    return null;
  }
  const platform = source.platform || fallbackPlatform;
  const blockedReasons = normalizeArray(source.blocked_reasons || source.blockedReasons);
  const hasIosReason = blockedReasons.some((reason) => String(reason).startsWith("IOS_"));
  if (platform !== "ios" && !hasIosReason) {
    return null;
  }
  return {
    platform: "ios",
    ready: Boolean(source.ready),
    checks: source.checks || {},
    missingFields: normalizeArray(source.missing_fields || source.missingFields),
    blockedReasons,
    nextActions: normalizeArray(source.next_actions || source.nextActions),
  };
}

function normalizeArray(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function statusClass(value) {
  if (!value) {
    return "";
  }
  if (["passed", "generated", "online", "ready", "validated", "confirmed", "clean", "redacted"].includes(value)) {
    return "ready";
  }
  if (["blocked", "failed", "unavailable", "offline", "cancelled", "privacy_blocked", "privacy_failed", "extract_failed", "validation_failed", "rejected"].includes(value)) {
    return "blocked";
  }
  return "warning";
}

function privacyStatusClass(value) {
  return statusClass(value);
}

function translatePlatform(value) {
  return PLATFORM_LABELS[value] || value || "-";
}

function translateRunMode(value) {
  return RUN_MODE_LABELS[value] || value || "-";
}

function translateStatus(value) {
  return STATUS_LABELS[value] || value || "-";
}

function translatePrivacyStatus(value) {
  return PRIVACY_LABELS[value] || translateStatus(value);
}

function translatePrivacyFinding(value) {
  return PRIVACY_FINDING_LABELS[value] || value || "-";
}

function translateDeviceKind(value) {
  return DEVICE_KIND_LABELS[value] || value || "-";
}

function translateTool(value) {
  return TOOL_LABELS[value] ? `${TOOL_LABELS[value]}（${value}）` : value;
}

function translateReason(value) {
  if (!value) {
    return "";
  }
  if (value.includes(",")) {
    return value.split(",").map(translateReason).join("、");
  }
  if (value.startsWith("ADB_STATE_")) {
    return `ADB 设备状态异常：${value.replace("ADB_STATE_", "")}`;
  }
  return REASON_LABELS[value] || value;
}

function translateNextAction(value) {
  return NEXT_ACTION_LABELS[value] || value;
}

function translateField(value) {
  return FIELD_LABELS[value] || value;
}

function translateEventMessage(value) {
  return EVENT_MESSAGE_LABELS[value] || value;
}

function translateSummary(value) {
  if (!value) {
    return "-";
  }
  if (value.startsWith("Run blocked: ")) {
    return `运行已阻断：${value.replace("Run blocked: ", "").split(", ").map(translateReason).join("、")}`;
  }
  const match = value.match(/^Run ([a-z_]+) for (.+)$/);
  if (match) {
    return `运行${translateStatus(match[1])}：${match[2]}`;
  }
  return value;
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
  return date.toLocaleString("zh-CN", { hour12: false });
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isSingleLine(value) {
  return !/[\r\n\u0000]/.test(value);
}

function showToast(message) {
  nodes.toast.textContent = message;
  nodes.toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    nodes.toast.classList.remove("visible");
  }, 3600);
}
