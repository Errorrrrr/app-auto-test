import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));

function createElement(tagName = "div") {
  return {
    tagName,
    children: [],
    className: "",
    textContent: "",
    disabled: false,
    firstChild: null,
    classList: {
      add() {},
      remove() {},
    },
    append(...items) {
      this.children.push(...items);
      this.firstChild = this.children[0] || null;
    },
    removeChild(child) {
      this.children = this.children.filter((item) => item !== child);
      this.firstChild = this.children[0] || null;
    },
  };
}

function collectText(node) {
  if (!node) {
    return "";
  }
  if (typeof node === "string") {
    return node;
  }
  const ownText = node.textContent || "";
  const childText = (node.children || []).map(collectText).join(" ");
  return `${ownText} ${childText}`.trim();
}

function loadApp() {
  class FakeFormData {
    constructor() {
      this.fields = [];
    }

    append(name, value) {
      this.fields.push([name, value]);
    }

    get(name) {
      return this.fields.find(([field]) => field === name)?.[1] ?? null;
    }
  }

  const context = {
    console,
    document: {
      addEventListener() {},
      createElement,
      getElementById: () => createElement(),
      querySelector: (selector) => {
        if (selector === "input[name='runMode']:checked") {
          return { value: "execute" };
        }
        if (selector === "input[name='agentProvider']:checked") {
          return { value: "codex" };
        }
        return { value: "android" };
      },
      querySelectorAll: () => [],
    },
    fetch: async () => {
      throw new Error("fetch stub was not configured");
    },
    FormData: FakeFormData,
    localStorage: {
      getItem: () => null,
      setItem() {},
    },
    window: {
      clearTimeout() {},
      location: { assign() {} },
      setTimeout: () => 1,
    },
  };
  vm.createContext(context);
  const source = readFileSync(new URL("../src/app_auto_test/web/app.js", import.meta.url), "utf8");
  vm.runInContext(
    `${source}\nglobalThis.__hooks = { api, createRun, nodes, normalizeTestcaseDraft, renderCapability, renderReport, renderTestcaseDraft, state };`,
    context,
  );
  return { context, hooks: context.__hooks };
}

function fetchIosCapabilityFromApi() {
  const code = `
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app_auto_test.config import Settings
from app_auto_test.main import create_app

with tempfile.TemporaryDirectory() as data_dir:
    app = create_app(Settings(data_dir=Path(data_dir)))
    client = TestClient(app)
    response = client.post("/api/v1/capabilities/check", data={"platform": "ios"})
    response.raise_for_status()
    print(json.dumps(response.json()["data"]))
`;
  const result = spawnSync("python3", ["-c", code], {
    cwd: repoRoot,
    encoding: "utf8",
    env: {
      ...process.env,
      PYTHONPATH: ["src", process.env.PYTHONPATH].filter(Boolean).join(":"),
    },
  });
  if (result.status !== 0) {
    throw new Error(`Failed to fetch iOS capability API response: ${result.stderr || result.stdout}`);
  }
  return JSON.parse(result.stdout);
}

test("api exposes backend 400 detail code and message", async () => {
  const { context, hooks } = loadApp();
  context.fetch = async () => ({
    ok: false,
    status: 400,
    headers: { get: () => "application/json" },
    json: async () => ({
      detail: {
        code: "CASE_FILE_YAML_UNSUPPORTED",
        message: "YAML files are not supported.",
      },
    }),
  });

  await assert.rejects(hooks.api("/api/v1/testcase-files"), (error) => {
    assert.equal(error.status, 400);
    assert.equal(error.code, "CASE_FILE_YAML_UNSUPPORTED");
    assert.equal(error.message, "YAML files are not supported.");
    return true;
  });
});

test("testcase failure panel renders real 400 error code", () => {
  const { hooks } = loadApp();
  hooks.nodes.testcaseFile = { files: [{ name: "flow.yaml" }] };
  hooks.nodes.testcasePanel = createElement();
  hooks.nodes.testcaseStatus = createElement();

  const error = new Error("YAML files are not supported.");
  error.code = "CASE_FILE_YAML_UNSUPPORTED";
  hooks.renderTestcaseDraft(error);

  assert.equal(hooks.nodes.testcaseStatus.textContent, "上传失败");
  assert.equal(hooks.nodes.testcaseStatus.className, "meta blocked");
  assert.match(hooks.nodes.testcasePanel.textContent, /不支持直接上传 YAML/);
  assert.match(hooks.nodes.testcasePanel.textContent, /YAML files are not supported/);
});

test("privacy findings accept backend type field", () => {
  const { hooks } = loadApp();
  const draft = hooks.normalizeTestcaseDraft({
    privacy_findings: [{ type: "email", count: "2", severity: "warning" }],
  });

  assert.equal(draft.privacy_findings[0].kind, "email");
  assert.equal(draft.privacy_findings[0].type, "email");
  assert.equal(draft.privacy_findings[0].count, 2);
});

test("create run sends confirmed draft review fields", async () => {
  const { context, hooks } = loadApp();
  let capturedBody = null;
  context.fetch = async (_path, options) => {
    capturedBody = options.body;
    throw new Error("stop after capture");
  };
  hooks.nodes.apkFile = { files: [{ name: "app.apk" }] };
  hooks.nodes.testName = { value: "confirmed draft run" };
  hooks.nodes.deviceSelect = { value: "emulator-5554" };
  hooks.nodes.packageName = { value: "com.example.app" };
  hooks.nodes.flowEditor = {
    value: JSON.stringify({
      name: "login flow",
      steps: [{ action: "launchApp" }],
    }),
  };
  hooks.nodes.createButton = createElement("button");
  hooks.nodes.toast = createElement();
  hooks.state.flowConfirmed = true;
  hooks.state.testcaseDraft = {
    draft_id: "draft-123",
    flow_review_status: "confirmed",
    confirmed_flow_hash: "sha256:abc",
    privacy_status: "redacted",
  };

  await hooks.createRun({ preventDefault() {} });

  assert.equal(capturedBody.get("sample_mode"), "provided");
  assert.equal(capturedBody.get("flow_review_status"), "confirmed");
  assert.equal(capturedBody.get("flow_draft_id"), "draft-123");
  assert.match(capturedBody.get("flow_json"), /login flow/);
});

test("iOS capability renders readiness blocked checklist", () => {
  const { hooks } = loadApp();
  hooks.nodes.capabilityReady = createElement();
  hooks.nodes.capabilityPanel = createElement();

  const capability = fetchIosCapabilityFromApi();
  assert.equal(capability.platform, "ios");
  assert.equal(capability.ready, false);
  assert.deepEqual(capability.missing_fields, ["ipa", "bundleId", "signingProfile", "targetDevice"]);
  assert.equal(Object.hasOwn(capability.checks, "runnerConfigured"), false);
  assert.equal(capability.blocked_reasons.includes("IOS_RUNNER_MISSING"), false);

  hooks.renderCapability(capability);

  const text = collectText(hooks.nodes.capabilityPanel);
  assert.match(text, /iOS readiness blocked 清单/);
  assert.match(text, /IPA/);
  assert.match(text, /bundleId/);
  assert.match(text, /签名配置/);
  assert.match(text, /目标设备/);
  assert.match(text, /Runner 路线/);
  assert.match(text, /不得启动真实 iOS runner/);
});

test("report preview renders iOS readiness from event capability details", () => {
  const { hooks } = loadApp();
  hooks.nodes.reportView = createElement();

  hooks.renderReport({
    report: {
      run_id: "run-ios",
      status: "blocked",
      result_summary: "Run blocked: IOS_SIGNING_MISSING",
      next_actions: [],
    },
    run: {
      run_id: "run-ios",
      platform: "ios",
      blocked_reasons: ["IOS_SIGNING_MISSING"],
      next_actions: [],
    },
    events: [
      {
        event_type: "HEALTH_CHECKED",
        details: {
          platform: "ios",
          ready: false,
          checks: {
            iosArtifactProvided: false,
            bundleIdProvided: false,
            signingReady: false,
            deviceAvailable: false,
            runnerConfigured: false,
          },
          missing_fields: ["ipa", "bundleId", "signingProfile", "targetDevice", "runnerType"],
          blocked_reasons: ["IOS_SIGNING_MISSING", "IOS_RUNNER_MISSING"],
          next_actions: [
            "Provide IPA, bundleId, signing method and a target iOS device or simulator before real iOS execution.",
          ],
        },
      },
    ],
    artifacts: [],
    generatedAt: "2026-06-16T06:18:44Z",
  });

  const text = collectText(hooks.nodes.reportView);
  assert.match(text, /iOS readiness blocked 清单/);
  assert.match(text, /签名配置/);
  assert.match(text, /Runner 路线/);
  assert.match(text, /不得启动真实 iOS runner/);
});
