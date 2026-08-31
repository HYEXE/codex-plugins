(() => {
  "use strict";

  const deck = window.INTERACTIVE_DECK;
  const sceneFactory = window.InteractiveSlideScenes;
  if (!deck?.meta || !Array.isArray(deck.slides) || deck.slides.length === 0 || !sceneFactory) {
    document.body.textContent = "유효한 deck.js와 scenes.js가 필요합니다.";
    return;
  }

  const byId = (id) => document.getElementById(id);
  const elements = {
    app: byId("app"), viewport: byId("viewport"), stageWrap: byId("stageWrap"), stage: byId("stage"),
    deckTitle: byId("deckTitle"), sectionName: byId("sectionName"), mode: byId("modeBtn"), replay: byId("replayBtn"),
    zoomOut: byId("zoomOut"), zoomIn: byId("zoomIn"), zoomText: byId("zoomText"), fit: byId("fitBtn"), full: byId("fullBtn"),
    outline: byId("outline"), outlineButton: byId("outlineBtn"), outlineClose: byId("outlineClose"), outlineList: byId("outlineList"), scrim: byId("scrim"),
    notes: byId("speakerNotes"), notesButton: byId("notesBtn"), notesClose: byId("notesClose"), notesContent: byId("notesContent"),
    previous: byId("previousBtn"), next: byId("nextBtn"), current: byId("currentNumber"), total: byId("totalNumber"), currentTitle: byId("currentTitle"),
    progress: byId("progressTrack"), progressFill: byId("progressFill"), toast: byId("toast")
  };

  const params = new URLSearchParams(window.location.search);
  const hashMatch = window.location.hash.match(/slide=(\d+)/);
  const requestedMode = params.get("mode");
  const modeLocked = deck.meta.modeLocked === true;
  const state = {
    index: Math.max(0, Math.min(deck.slides.length - 1, hashMatch ? Number(hashMatch[1]) - 1 : 0)),
    mode: !modeLocked && ["experience", "demo"].includes(requestedMode)
      ? requestedMode
      : deck.meta.defaultMode,
    zoom: 1,
    fitScale: 1,
    scene: null,
    toastTimer: 0,
    touchX: 0,
    touchY: 0,
    touchStartedOnControl: false,
    outlineReturnFocus: null
  };
  if (!["experience", "demo"].includes(state.mode)) state.mode = "demo";
  if (modeLocked) {
    elements.mode.hidden = true;
    elements.mode.disabled = true;
    elements.mode.setAttribute("aria-hidden", "true");
  }

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
  const currentSlide = () => deck.slides[state.index];

  function announce(message) {
    window.clearTimeout(state.toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.add("show");
    state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 1800);
  }

  function renderSlide() {
    state.scene?.destroy();
    state.scene = null;
    elements.stageWrap.classList.remove("static-fallback-wrap");
    elements.stage.classList.remove("has-static-fallback");
    const slide = currentSlide();
    const evidence = slide.evidence ? `<span class="evidence ${escapeHtml(slide.evidence.tone)}">${escapeHtml(slide.evidence.label)}</span>` : "";
    const body = Array.isArray(slide.body) ? `<div class="body-copy">${slide.body.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}</div>` : "";
    const points = Array.isArray(slide.points) ? `<ul class="points">${slide.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>` : "";
    const metrics = Array.isArray(slide.metrics) ? `<div class="metrics">${slide.metrics.map((metric) => `<article class="metric"><b>${escapeHtml(metric.value)}<small>${escapeHtml(metric.unit)}</small></b><span>${escapeHtml(metric.label)}</span><em>${escapeHtml(metric.detail)}</em></article>`).join("")}</div>` : "";
    const scene = slide.scene ? `<div id="sceneMount"><div class="scene-fallback"><strong>정적 설명</strong><p>${escapeHtml(slide.fallback || slide.summary || "장면을 표시할 수 없습니다.")}</p></div></div>` : "";
    const sources = (slide.sources || []).map(escapeHtml).join(" · ");
    elements.stage.innerHTML = `<article class="slide"><header class="slide-head"><span class="slide-number">${String(state.index + 1).padStart(2, "0")}</span><div class="slide-heading"><p class="kicker">${escapeHtml(slide.kicker || slide.section)}</p><h1>${escapeHtml(slide.title)}</h1></div>${evidence}</header><div class="slide-body"><p class="summary">${escapeHtml(slide.summary || "")}</p>${body}${points}${metrics}${scene}</div><footer class="slide-footer"><span class="source-list">${sources}</span><span>${String(state.index + 1).padStart(2, "0")} / ${String(deck.slides.length).padStart(2, "0")}</span></footer></article>`;
    elements.notesContent.innerHTML = `<ul>${(slide.notes || []).map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>`;
    if (slide.scene) {
      try {
        state.scene = sceneFactory.create(byId("sceneMount"), slide.scene, {
          mode: state.mode,
          announce,
          onStatusChange: updateNextLabel
        });
      } catch (error) {
        byId("sceneMount").innerHTML = `<div class="scene-fallback"><strong>장면 fallback</strong><p>${escapeHtml(slide.fallback || slide.summary || "장면을 표시할 수 없습니다.")}</p></div>`;
        console.error("Interactive slide scene failed", error);
        announce("시연 장면 대신 정적 설명을 표시합니다");
      }
    }
    updateChrome();
  }

  function updateNextLabel() {
    if (state.mode === "demo" && state.scene?.blocksAdvance) {
      if (state.scene.status === "ready") elements.next.textContent = "시연 시작";
      else if (state.scene.status === "running") elements.next.textContent = "건너뛰기";
      else elements.next.textContent = "다음";
    } else elements.next.textContent = "다음";
  }

  function updateChrome() {
    const slide = currentSlide();
    elements.sectionName.textContent = slide.section || "발표";
    elements.current.textContent = String(state.index + 1).padStart(2, "0");
    elements.total.textContent = String(deck.slides.length).padStart(2, "0");
    elements.currentTitle.textContent = slide.title;
    elements.progress.setAttribute("aria-valuenow", String(state.index + 1));
    elements.progress.setAttribute("aria-valuemax", String(deck.slides.length));
    elements.progress.setAttribute("aria-valuetext", `${state.index + 1} / ${deck.slides.length} · ${slide.title}`);
    elements.progressFill.style.width = `${(state.index + 1) / deck.slides.length * 100}%`;
    elements.previous.disabled = state.index === 0;
    elements.next.disabled = state.index === deck.slides.length - 1 && !(state.mode === "demo" && state.scene?.blocksAdvance && state.scene.status !== "complete");
    elements.mode.textContent = state.mode === "demo" ? "시연형" : "체험형";
    elements.mode.setAttribute("aria-pressed", String(state.mode === "experience"));
    elements.outlineList.querySelectorAll(".outline-item").forEach((button, index) => button.setAttribute("aria-current", index === state.index ? "page" : "false"));
    updateNextLabel();
  }

  function go(nextIndex, updateHash = true) {
    const bounded = Math.max(0, Math.min(deck.slides.length - 1, nextIndex));
    if (bounded === state.index && elements.stage.firstElementChild) return;
    state.scene?.cancel();
    state.index = bounded;
    if (updateHash) history.replaceState(null, "", `#slide=${state.index + 1}`);
    renderSlide();
  }

  function advanceForward() {
    if (state.mode === "demo" && state.scene?.blocksAdvance) {
      if (state.scene.status === "ready") { state.scene.start(); updateNextLabel(); return; }
      if (state.scene.status === "running") {
        state.scene.cancel();
        announce("현재 시연을 건너뛰었습니다");
        go(state.index + 1);
        return;
      }
    }
    go(state.index + 1);
  }

  function replayCurrent() {
    elements.stage.classList.remove("replay");
    requestAnimationFrame(() => requestAnimationFrame(() => elements.stage.classList.add("replay")));
    if (state.scene) state.scene.replay(state.mode === "demo" && state.scene.blocksAdvance);
    announce("현재 장면을 다시 재생합니다");
    updateNextLabel();
  }

  function setMode(mode) {
    if (modeLocked) return;
    state.scene?.cancel();
    state.mode = mode;
    const url = new URL(window.location.href);
    url.searchParams.set("mode", mode);
    history.replaceState(null, "", `${url.pathname}${url.search}#slide=${state.index + 1}`);
    renderSlide();
    announce(mode === "demo" ? "시연형 모드" : "체험형 모드");
  }

  function fitStage() {
    const mobileReflow = window.matchMedia("(max-width: 720px)").matches;
    elements.app.classList.toggle("mobile-reflow", mobileReflow);
    if (mobileReflow) {
      state.fitScale = 1;
      applyScale();
      return;
    }
    const availableWidth = Math.max(320, elements.viewport.clientWidth - 40);
    const availableHeight = Math.max(180, elements.viewport.clientHeight - 40);
    state.fitScale = Math.min(availableWidth / 1600, availableHeight / 900);
    applyScale();
  }

  function applyScale() {
    if (elements.app.classList.contains("mobile-reflow")) {
      elements.stage.style.removeProperty("transform");
      elements.stageWrap.style.removeProperty("width");
      elements.stageWrap.style.removeProperty("height");
      elements.zoomText.textContent = "100%";
      return;
    }
    const scale = Math.max(0.2, Math.min(2, state.fitScale * state.zoom));
    elements.stage.style.transform = `scale(${scale})`;
    elements.stageWrap.style.width = `${1600 * scale}px`;
    elements.stageWrap.style.height = `${900 * scale}px`;
    elements.zoomText.textContent = `${Math.round(state.zoom * 100)}%`;
  }

  function setZoom(value) { state.zoom = Math.max(0.5, Math.min(1.8, value)); applyScale(); }

  function buildOutline() {
    let section = "";
    deck.slides.forEach((slide, index) => {
      if (slide.section !== section) {
        section = slide.section;
        const heading = document.createElement("div");
        heading.className = "outline-group";
        heading.textContent = section;
        elements.outlineList.appendChild(heading);
      }
      const button = document.createElement("button");
      button.type = "button";
      button.className = "outline-item";
      button.innerHTML = `<b>${String(index + 1).padStart(2, "0")}</b><span>${escapeHtml(slide.title)}</span>`;
      button.addEventListener("click", () => { go(index); closeOutline(); });
      elements.outlineList.appendChild(button);
    });
  }

  function outlineFocusables() { return [...elements.outline.querySelectorAll("button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])")]; }
  function openOutline() {
    state.outlineReturnFocus = document.activeElement;
    elements.outline.inert = false;
    elements.outline.classList.add("open");
    elements.scrim.classList.add("show");
    elements.outline.setAttribute("aria-hidden", "false");
    elements.outlineButton.setAttribute("aria-expanded", "true");
    elements.outlineClose.focus();
  }
  function closeOutline() {
    elements.outline.classList.remove("open");
    elements.scrim.classList.remove("show");
    elements.outline.setAttribute("aria-hidden", "true");
    elements.outlineButton.setAttribute("aria-expanded", "false");
    elements.outline.inert = true;
    state.outlineReturnFocus?.focus();
  }
  function toggleOutline() { elements.outline.classList.contains("open") ? closeOutline() : openOutline(); }

  async function toggleFullscreen() {
    try { document.fullscreenElement ? await document.exitFullscreen() : await elements.app.requestFullscreen({ navigationUI: "hide" }); }
    catch { announce("전체화면을 허용하지 않았습니다"); }
  }

  function toggleNotes(force) {
    const open = typeof force === "boolean" ? force : elements.notes.hidden;
    elements.notes.hidden = !open;
    elements.notesButton.setAttribute("aria-expanded", String(open));
  }

  function onKeydown(event) {
    if (elements.outline.classList.contains("open")) {
      if (event.key === "Escape") { event.preventDefault(); closeOutline(); return; }
      if (event.key === "Tab") {
        const focusables = outlineFocusables();
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
      return;
    }
    const onControl = event.target instanceof Element && event.target.closest("button,a,input,textarea,select,[contenteditable='true'],[role='slider'],[role='tab'],[role='menuitem'],[role='option']");
    if (onControl) return;
    if (["ArrowRight", "PageDown", " ", "Enter"].includes(event.key)) { event.preventDefault(); advanceForward(); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(event.key)) { event.preventDefault(); go(state.index - 1); }
    else if (event.key === "Home") { event.preventDefault(); go(0); }
    else if (event.key === "End") { event.preventDefault(); go(deck.slides.length - 1); }
    else if (event.key.toLowerCase() === "o") { event.preventDefault(); toggleOutline(); }
    else if (event.key.toLowerCase() === "n") { event.preventDefault(); toggleNotes(); }
    else if (event.key.toLowerCase() === "r") { event.preventDefault(); replayCurrent(); }
    else if (event.key.toLowerCase() === "f") { event.preventDefault(); toggleFullscreen(); }
    else if (["+", "="].includes(event.key)) { event.preventDefault(); setZoom(state.zoom + 0.1); }
    else if (["-", "_"].includes(event.key)) { event.preventDefault(); setZoom(state.zoom - 0.1); }
    else if (event.key === "0") { event.preventDefault(); state.zoom = 1; fitStage(); announce("화면에 맞췄습니다"); }
  }

  elements.deckTitle.textContent = deck.meta.title;
  document.title = deck.meta.title;
  elements.previous.addEventListener("click", () => go(state.index - 1));
  elements.next.addEventListener("click", advanceForward);
  if (!modeLocked) {
    elements.mode.addEventListener("click", () =>
      setMode(state.mode === "demo" ? "experience" : "demo")
    );
  }
  elements.replay.addEventListener("click", replayCurrent);
  elements.zoomIn.addEventListener("click", () => setZoom(state.zoom + 0.1));
  elements.zoomOut.addEventListener("click", () => setZoom(state.zoom - 0.1));
  elements.fit.addEventListener("click", () => { state.zoom = 1; fitStage(); });
  elements.full.addEventListener("click", toggleFullscreen);
  elements.outlineButton.addEventListener("click", toggleOutline);
  elements.outlineClose.addEventListener("click", closeOutline);
  elements.scrim.addEventListener("click", closeOutline);
  elements.notesButton.addEventListener("click", () => toggleNotes());
  elements.notesClose.addEventListener("click", () => toggleNotes(false));
  elements.progress.addEventListener("click", (event) => {
    const rect = elements.progress.getBoundingClientRect();
    go(Math.min(deck.slides.length - 1, Math.floor((event.clientX - rect.left) / rect.width * deck.slides.length)));
  });
  elements.progress.addEventListener("keydown", (event) => {
    if (["ArrowRight", "ArrowUp"].includes(event.key)) { event.preventDefault(); go(state.index + 1); }
    if (["ArrowLeft", "ArrowDown"].includes(event.key)) { event.preventDefault(); go(state.index - 1); }
  });
  document.addEventListener("keydown", onKeydown);
  window.addEventListener("resize", fitStage);
  window.addEventListener("hashchange", () => {
    const match = window.location.hash.match(/slide=(\d+)/);
    if (match) go(Number(match[1]) - 1, false);
  });
  document.addEventListener("touchstart", (event) => {
    state.touchX = event.changedTouches[0].clientX;
    state.touchY = event.changedTouches[0].clientY;
    state.touchStartedOnControl = Boolean(
      event.target.closest(
        "button, a, input, textarea, select, [role='button'], [role='slider'], [role='tab'], [contenteditable='true']"
      )
    );
  }, { passive: true });
  document.addEventListener("touchend", (event) => {
    const startedOnControl = state.touchStartedOnControl;
    state.touchStartedOnControl = false;
    if (startedOnControl) return;
    const x = event.changedTouches[0].clientX - state.touchX;
    const y = event.changedTouches[0].clientY - state.touchY;
    if (Math.abs(x) > 60 && Math.abs(x) > Math.abs(y) * 1.2) go(state.index + (x < 0 ? 1 : -1));
  }, { passive: true });

  document.addEventListener("touchcancel", () => {
    state.touchStartedOnControl = false;
  }, { passive: true });

  buildOutline();
  renderSlide();
  fitStage();
})();

// Authoring decisions are locked before generation. Presentation chrome exposes
// utilities as accessible icons and never asks the audience to choose a mode.
const AUTHORING_ICON_PATHS = {
  outline: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  replay: '<path d="M4 10a8 8 0 1 1 2 7"/><path d="M4 4v6h6"/>',
  zoomOut: '<path d="M5 12h14"/>',
  zoomIn: '<path d="M12 5v14M5 12h14"/>',
  fit: '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
  fullscreen: '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
  notes: '<path d="M5 3h14v18H5z"/><path d="M8 8h8M8 12h8M8 16h5"/>'
};

const AUTHORING_ICON_CONTROLS = [
  { scope: 'header', match: /발표 목차|^목차$/, label: '발표 목차', icon: 'outline' },
  { scope: 'header', match: /다시 보기/, label: '현재 장면 다시 보기', icon: 'replay' },
  { scope: 'header', match: /축소/, label: '축소', icon: 'zoomOut' },
  { scope: 'header', match: /확대/, label: '확대', icon: 'zoomIn' },
  { scope: 'header', match: /맞춤/, label: '화면 맞춤', icon: 'fit' },
  { scope: 'header', match: /전체화면/, label: '전체화면', icon: 'fullscreen' },
  { scope: 'footer', match: /^노트$/, label: '발표자 노트', icon: 'notes' }
];

function lockAuthoringMode() {
  if (window.INTERACTIVE_DECK?.meta?.modeLocked !== true) return;
  const requested = (
    document.documentElement.dataset.presentationMode ||
    document.body?.dataset.presentationMode ||
    'demo'
  ).toLowerCase();
  const mode = requested === 'experience' ? 'experience' : 'demo';
  document.documentElement.dataset.presentationMode = mode;

  const toggle = [...document.querySelectorAll('header button')].find((button) =>
    /^(시연형|체험형)$/.test(button.textContent.trim())
  );

  if (!toggle) return;
  const current = toggle.textContent.trim() === '체험형' ? 'experience' : 'demo';
  if (current !== mode) toggle.click();
  toggle.remove();
}

function renderAuthoringIcons() {
  lockAuthoringMode();

  for (const control of AUTHORING_ICON_CONTROLS) {
    const button = [...document.querySelectorAll(control.scope + ' button')].find(
      (candidate) =>
        !candidate.classList.contains('icon-control') &&
        control.match.test(
          candidate.getAttribute('aria-label') || candidate.textContent.trim()
        )
    );

    if (!button) continue;
    button.classList.add('icon-control');
    button.setAttribute('aria-label', control.label);
    button.setAttribute('title', control.label);
    button.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      AUTHORING_ICON_PATHS[control.icon] +
      '</svg>';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderAuthoringIcons, { once: true });
} else {
  renderAuthoringIcons();
}

const authoringChromeObserver = new MutationObserver(renderAuthoringIcons);
authoringChromeObserver.observe(document.documentElement, {
  childList: true,
  subtree: true
});
