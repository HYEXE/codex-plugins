const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");

const REPOSITORY_ROOT = path.resolve(__dirname, "..", "..");
const SKILL_ROOT = path.join(
  REPOSITORY_ROOT,
  "plugins",
  "interactive-slides",
  "skills",
  "create-interactive-slides"
);
const STARTER_ROOT = path.join(SKILL_ROOT, "assets", "starter");
const FIXTURE_ROOT = path.join(SKILL_ROOT, "evals", "forward", "fixtures");
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

let temporaryRoot;
let server;
let baseURL;

function createProject(name, fixtureName, transformDeck = (deck) => deck) {
  const project = path.join(temporaryRoot, name);
  fs.cpSync(STARTER_ROOT, project, { recursive: true });
  const source = path.join(FIXTURE_ROOT, fixtureName, "deck.js");
  const original = fs.readFileSync(source, "utf8");
  const transformed = transformDeck(original);
  fs.writeFileSync(path.join(project, "deck.js"), transformed, "utf8");
}

function startStaticServer(root) {
  const rootPrefix = path.resolve(root) + path.sep;
  const instance = http.createServer((request, response) => {
    const requestURL = new URL(request.url, "http://127.0.0.1");
    const decodedPath = decodeURIComponent(requestURL.pathname);
    const relativePath = decodedPath.replace(/^\/+/, "");
    let target = path.resolve(root, relativePath);
    if (decodedPath.endsWith("/")) {
      target = path.join(target, "index.html");
    }
    if (target !== path.resolve(root) && !target.startsWith(rootPrefix)) {
      response.writeHead(403).end("Forbidden");
      return;
    }
    fs.readFile(target, (error, data) => {
      if (error) {
        response.writeHead(error.code === "ENOENT" ? 404 : 500).end("Not found");
        return;
      }
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": MIME_TYPES[path.extname(target)] || "application/octet-stream",
      });
      response.end(data);
    });
  });
  return new Promise((resolve, reject) => {
    instance.once("error", reject);
    instance.listen(0, "127.0.0.1", () => {
      const address = instance.address();
      resolve({
        instance,
        url: "http://127.0.0.1:" + address.port,
      });
    });
  });
}

async function openDeck(page, project, location = "") {
  await page.goto(
    baseURL + "/" + project + "/index.html" + location,
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#stage .slide")).toBeVisible();
}

test.beforeAll(async () => {
  temporaryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "interactive-slides-browser-")
  );
  createProject("demo", "demo-release-control-room");
  createProject("experience", "experience-scenario-lab");
  createProject(
    "unlocked-demo",
    "demo-release-control-room",
    (deck) => deck.replace("modeLocked: true", "modeLocked: false")
  );
  const listening = await startStaticServer(temporaryRoot);
  server = listening.instance;
  baseURL = listening.url;
});

test.afterAll(async () => {
  if (server) {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
      server.closeAllConnections();
    });
  }
  if (temporaryRoot) {
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
  }
});

test("locked demo ignores query and keyboard mode changes", async ({ page }) => {
  await openDeck(page, "demo", "?mode=experience#slide=2");

  await expect(page.locator("#modeBtn")).toBeHidden();
  await expect(page.locator("#nextBtn")).toHaveText("시연 시작");

  await page.keyboard.press("m");
  await expect(page.locator("#nextBtn")).toHaveText("시연 시작");
  await expect(page).toHaveURL(/mode=experience#slide=2$/);
});

test("unlocked deck keeps query, button and keyboard mode controls", async ({ page }) => {
  await openDeck(page, "unlocked-demo", "?mode=experience#slide=2");

  const modeButton = page.locator("#modeBtn");
  await expect(modeButton).toBeVisible();
  await expect(modeButton).toHaveText("체험형");
  await expect(page.locator("#nextBtn")).toHaveText("다음");

  await modeButton.click();
  await expect(modeButton).toHaveText("시연형");
  await expect(page.locator("#nextBtn")).toHaveText("시연 시작");
  await expect(page).toHaveURL(/mode=demo#slide=2$/);

  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press("m");
  await expect(modeButton).toHaveText("체험형");
  await expect(page.locator("#nextBtn")).toHaveText("다음");
});

test("demo sequence reaches complete before advancing", async ({ page }) => {
  await openDeck(page, "demo", "#slide=2");

  const next = page.locator("#nextBtn");
  await expect(next).toHaveText("시연 시작");
  await next.click();
  await expect(next).toHaveText("건너뛰기");
  await expect(next).toHaveText("다음", { timeout: 15_000 });
  await next.click();
  await expect(page).toHaveURL(/#slide=3$/);
});

test("experience range preserves native keys and replay reset", async ({ page }) => {
  await openDeck(page, "experience", "#slide=2");

  const range = page.locator('#sceneMount input[type="range"]');
  await expect(range).toBeVisible();
  const initialValue = await range.inputValue();

  await range.focus();
  await page.keyboard.press("ArrowRight");
  const changedValue = await range.inputValue();
  expect(Number(changedValue)).toBeGreaterThan(Number(initialValue));
  await expect(page).toHaveURL(/#slide=2$/);

  await page.locator("#replayBtn").click();
  await expect(page.locator('#sceneMount input[type="range"]')).toHaveValue(
    initialValue
  );
});

test("reduced motion completes blocking scenes without timed animation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await openDeck(page, "demo", "#slide=2");

  expect(
    await page.evaluate(() =>
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    )
  ).toBe(true);
  const next = page.locator("#nextBtn");
  await next.click();
  await expect(next).toHaveText("다음", { timeout: 1_500 });
});

test("mobile viewport uses reflow without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openDeck(page, "experience", "#slide=3");

  await expect(page.locator("#app")).toHaveClass(/mobile-reflow/);
  const layout = await page.evaluate(() => ({
    stageTransform: document.getElementById("stage").style.transform,
    wrapWidth: document.getElementById("stageWrap").style.width,
    viewportWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
  }));
  expect(layout.stageTransform).toBe("");
  expect(layout.wrapWidth).toBe("");
  expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth + 1);
});

test("icon-only chrome keeps accessible names and tooltips", async ({ page }) => {
  await openDeck(page, "demo");

  const controls = page.locator("button.icon-control");
  expect(await controls.count()).toBeGreaterThanOrEqual(6);
  const contracts = await controls.evaluateAll((buttons) =>
    buttons.map((button) => ({
      label: button.getAttribute("aria-label"),
      title: button.getAttribute("title"),
      svg: Boolean(button.querySelector("svg[aria-hidden='true']")),
    }))
  );
  for (const contract of contracts) {
    expect(contract.label).toBeTruthy();
    expect(contract.title).toBe(contract.label);
    expect(contract.svg).toBe(true);
  }
});
