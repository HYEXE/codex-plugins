(() => {
  "use strict";

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);

  class SceneController {
    constructor(root, config, context) {
      this.root = root;
      this.config = config;
      this.context = context;
      this.status = "ready";
      this.blocksAdvance = false;
    }
    setStatus(status) {
      this.status = status;
      this.context.onStatusChange?.(status);
    }
    start() {}
    advance() {}
    skip() {}
    replay() {}
    cancel() {}
    destroy() { this.cancel(); }
  }

  class SequenceScene extends SceneController {
    constructor(root, config, context) {
      super(root, config, context);
      this.blocksAdvance = true;
      this.index = 0;
      this.runToken = 0;
      this.timers = [];
      this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.render();
    }
    render() {
      const nodes = this.config.nodes || this.config.phases.map((_, index) => `STEP ${index + 1}`);
      this.root.innerHTML = `<div class="scene sequence-shell" data-state="ready">
        <div class="sequence-bar"><span class="window-lights" aria-hidden="true"><i></i><i></i><i></i></span><strong class="sequence-label">${escapeHtml(this.config.label || "SYNTHETIC TELEMETRY")}</strong><span class="sequence-status" aria-live="polite">READY · 0 / ${this.config.phases.length}</span></div>
        <div class="sequence-route" style="--node-count:${nodes.length}">${nodes.map((node, index) => `<span class="route-node" data-node="${index}">${escapeHtml(node)}</span>`).join("")}</div>
        <div class="sequence-main"><section class="phase-card"><small>READY</small><h2>시연 준비</h2><p>다음 동작으로 장면을 시작합니다.</p><div class="scene-actions"><button type="button" data-scene-next>단계 실행</button></div></section><div class="sequence-log" role="log" aria-live="polite" aria-relevant="additions"><p class="log-line system">[READY] 재생 가능한 초기 상태입니다.</p></div></div>
      </div>`;
      this.shell = this.root.querySelector(".sequence-shell");
      this.statusText = this.root.querySelector(".sequence-status");
      this.phaseCard = this.root.querySelector(".phase-card");
      this.log = this.root.querySelector(".sequence-log");
      this.nextButton = this.root.querySelector("[data-scene-next]");
      this.nextButton.addEventListener("click", () => this.advance());
    }
    clearTimers() {
      this.timers.forEach(window.clearTimeout);
      this.timers = [];
    }
    schedule(callback, delay, token) {
      const timer = window.setTimeout(() => {
        if (token === this.runToken) callback();
      }, delay);
      this.timers.push(timer);
    }
    showPhase(phaseIndex) {
      const phase = this.config.phases[phaseIndex];
      if (!phase) return;
      this.index = phaseIndex + 1;
      this.shell.dataset.state = phase.tone || "active";
      this.statusText.textContent = `RUNNING · ${this.index} / ${this.config.phases.length}`;
      this.phaseCard.querySelector("small").textContent = phase.kicker || `PHASE ${String(this.index).padStart(2, "0")}`;
      this.phaseCard.querySelector("h2").textContent = phase.title;
      this.phaseCard.querySelector("p").textContent = phase.detail;
      this.root.querySelectorAll("[data-node]").forEach((node, index) => {
        node.classList.toggle("active", index === phaseIndex);
        node.classList.toggle("complete", index < phaseIndex);
      });
      (phase.lines || []).forEach((line) => {
        const item = document.createElement("p");
        item.className = `log-line ${line.kind || "system"}`;
        item.textContent = line.text;
        this.log.appendChild(item);
      });
      this.log.scrollTop = this.log.scrollHeight;
      if (this.index >= this.config.phases.length) this.complete();
    }
    complete() {
      this.clearTimers();
      this.setStatus("complete");
      this.shell.dataset.state = "complete";
      this.statusText.textContent = `COMPLETE · ${this.config.phases.length} / ${this.config.phases.length}`;
      this.root.querySelectorAll("[data-node]").forEach((node) => { node.classList.remove("active"); node.classList.add("complete"); });
      this.nextButton.textContent = "처음으로";
      this.nextButton.disabled = false;
      this.context.announce?.("시연 장면이 완료됐습니다");
    }
    start() {
      this.reset();
      this.setStatus("running");
      this.nextButton.disabled = true;
      const token = ++this.runToken;
      const interval = this.reducedMotion ? 45 : 1450;
      this.config.phases.forEach((_, index) => this.schedule(() => this.showPhase(index), index * interval + (this.reducedMotion ? 10 : 180), token));
      this.schedule(() => { this.nextButton.disabled = false; }, this.config.phases.length * interval + 220, token);
      this.context.announce?.("자동 시연을 시작합니다");
    }
    advance() {
      if (this.status === "complete") { this.reset(); return; }
      if (this.status === "ready") this.setStatus("running");
      this.showPhase(this.index);
    }
    skip() {
      this.clearTimers();
      this.runToken += 1;
      while (this.index < this.config.phases.length) this.showPhase(this.index);
      this.complete();
    }
    replay(autoplay = false) {
      this.reset();
      if (autoplay) this.start();
    }
    reset() {
      this.cancel();
      this.index = 0;
      this.setStatus("ready");
      this.render();
    }
    cancel() {
      this.runToken += 1;
      this.clearTimers();
      if (this.nextButton) this.nextButton.disabled = false;
    }
  }

  class InteractionScene extends SceneController {
    constructor(root, config, context) {
      super(root, config, context);
      this.render();
    }
    render() {
      if (this.config.type === "steps") this.renderSteps();
      if (this.config.type === "comparison") this.renderComparison();
      if (this.config.type === "choice") this.renderChoice();
      if (this.config.type === "range") this.renderRange();
      if (this.config.type === "diagram") this.renderDiagram();
      if (this.config.type === "before-after") this.renderBeforeAfter();
    }
    renderSteps() {
      this.root.innerHTML = `<div class="scene"><div class="scene-grid">${this.config.items.map((item, index) => `<button class="scene-card" type="button" data-step="${index}" aria-current="${index === 0 ? "step" : "false"}"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.detail)}</span></button>`).join("")}</div></div>`;
      this.root.querySelectorAll("[data-step]").forEach((button) => button.addEventListener("click", () => {
        this.root.querySelectorAll("[data-step]").forEach((item) => item.setAttribute("aria-current", "false"));
        button.setAttribute("aria-current", "step");
      }));
    }
    renderComparison() {
      const column = (side) => `<section><h2>${escapeHtml(side.label)}</h2><ul>${side.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul></section>`;
      this.root.innerHTML = `<div class="scene comparison">${column(this.config.left)}${column(this.config.right)}</div>`;
    }
    renderChoice() {
      this.root.innerHTML = `<div class="scene"><p>${escapeHtml(this.config.prompt)}</p><div class="choice-grid">${this.config.options.map((option, index) => `<button class="choice" type="button" data-choice="${index}" aria-pressed="false">${escapeHtml(option.label)}</button>`).join("")}</div><p class="feedback" aria-live="polite"></p></div>`;
      this.root.querySelectorAll("[data-choice]").forEach((button) => button.addEventListener("click", () => {
        this.root.querySelectorAll("[data-choice]").forEach((item) => item.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        this.root.querySelector(".feedback").textContent = this.config.options[Number(button.dataset.choice)].feedback;
      }));
    }
    renderRange() {
      this.root.innerHTML = `<div class="scene range-scene"><label>${escapeHtml(this.config.label)}: <output data-range-value></output><input data-range type="range" min="${this.config.min}" max="${this.config.max}" step="${this.config.step}" value="${this.config.value}"></label><div class="range-output"><small>${escapeHtml(this.config.outputLabel)}</small><strong data-range-result></strong></div></div>`;
      const range = this.root.querySelector("[data-range]");
      const update = () => {
        const value = Number(range.value);
        const result = this.config.result || { base: 0, factor: 1, decimals: 0, suffix: "" };
        this.root.querySelector("[data-range-value]").textContent = `${value}${this.config.unit || ""}`;
        this.root.querySelector("[data-range-result]").textContent = `${(result.base + value * result.factor).toFixed(result.decimals || 0)}${result.suffix || ""}`;
      };
      range.addEventListener("input", update);
      update();
    }
    renderDiagram() {
      const nodeIds = new Set(this.config.nodes.map((node) => node.id));
      const validLinks = (this.config.links || []).filter((link) => nodeIds.has(link.from) && nodeIds.has(link.to));
      this.root.innerHTML = `<div class="scene diagram-scene"><div class="diagram-nodes">${this.config.nodes.map((node, index) => `<button type="button" class="diagram-node" data-node-id="${escapeHtml(node.id)}" aria-pressed="${index === 0 ? "true" : "false"}"><strong>${escapeHtml(node.label)}</strong><span>${escapeHtml(node.detail)}</span></button>`).join("")}</div><aside class="diagram-detail" aria-live="polite"><small>SELECTED NODE</small><strong></strong><p></p></aside><ul class="diagram-links" aria-label="노드 연결 관계">${validLinks.map((link) => `<li><b>${escapeHtml(link.from)}</b><span>→</span><b>${escapeHtml(link.to)}</b><em>${escapeHtml(link.label || "연결")}</em></li>`).join("")}</ul></div>`;
      const select = (node) => {
        this.root.querySelectorAll("[data-node-id]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.nodeId === node.id)));
        const detail = this.root.querySelector(".diagram-detail");
        detail.querySelector("strong").textContent = node.label;
        detail.querySelector("p").textContent = node.detail;
      };
      this.root.querySelectorAll("[data-node-id]").forEach((button) => button.addEventListener("click", () => select(this.config.nodes.find((node) => node.id === button.dataset.nodeId))));
      select(this.config.nodes[0]);
    }
    renderBeforeAfter() {
      const states = { before: this.config.before, after: this.config.after };
      this.root.innerHTML = `<div class="scene before-after-scene"><div class="before-after-tabs" role="group" aria-label="전후 상태"><button type="button" data-view="before" aria-pressed="true">${escapeHtml(this.config.before.label)}</button><button type="button" data-view="after" aria-pressed="false">${escapeHtml(this.config.after.label)}</button></div><article class="before-after-panel" aria-live="polite"><small></small><h2></h2><ul></ul></article></div>`;
      const show = (key) => {
        const selected = states[key];
        this.root.querySelectorAll("[data-view]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.view === key)));
        const panel = this.root.querySelector(".before-after-panel");
        panel.dataset.view = key;
        panel.querySelector("small").textContent = key.toUpperCase();
        panel.querySelector("h2").textContent = selected.label;
        panel.querySelector("ul").innerHTML = selected.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("");
      };
      this.root.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => show(button.dataset.view)));
      show("before");
    }
    replay() { this.render(); }
  }

  class ProgressiveScene extends SceneController {
    constructor(root, config, context) {
      super(root, config, context);
      this.blocksAdvance = true;
      this.index = 0;
      this.runToken = 0;
      this.timers = [];
      this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.render();
    }
    get items() { return this.config.type === "timeline" ? this.config.events : this.config.lines; }
    render() {
      if (this.config.type === "timeline") this.renderTimeline();
      else this.renderCode();
    }
    renderTimeline() {
      this.root.innerHTML = `<div class="scene progressive-scene timeline-scene" data-state="ready"><div class="timeline-track">${this.items.map((event, index) => `<button type="button" class="timeline-event" data-progressive-step="${index}" aria-pressed="false"><time>${escapeHtml(event.date)}</time><strong>${escapeHtml(event.title)}</strong></button>`).join("")}</div><article class="progressive-detail" aria-live="polite"><small>READY · 0 / ${this.items.length}</small><h2>타임라인 준비</h2><p>사건을 선택하거나 장면을 시작하세요.</p></article><div class="scene-actions"><button type="button" data-progressive-next>다음 사건</button></div></div>`;
      this.bindStepButtons();
    }
    renderCode() {
      this.root.innerHTML = `<div class="scene progressive-scene code-walkthrough-scene" data-state="ready"><div class="code-layout"><ol class="code-lines" aria-label="${escapeHtml(this.config.language || "code")} 코드">${this.items.map((line, index) => `<li><button type="button" data-progressive-step="${index}" aria-pressed="false"><code>${escapeHtml(line.code)}</code></button></li>`).join("")}</ol><article class="progressive-detail" aria-live="polite"><small>READY · 0 / ${this.items.length}</small><h2>코드 해설 준비</h2><p>코드 줄을 선택하거나 장면을 시작하세요.</p></article></div><div class="scene-actions"><button type="button" data-progressive-next>다음 줄</button></div></div>`;
      this.bindStepButtons();
    }
    bindStepButtons() {
      this.shell = this.root.querySelector(".progressive-scene");
      this.detail = this.root.querySelector(".progressive-detail");
      this.nextButton = this.root.querySelector("[data-progressive-next]");
      this.root.querySelectorAll("[data-progressive-step]").forEach((button) => button.addEventListener("click", () => this.showStep(Number(button.dataset.progressiveStep))));
      this.nextButton.addEventListener("click", () => this.advance());
    }
    clearTimers() { this.timers.forEach(window.clearTimeout); this.timers = []; }
    schedule(callback, delay, token) {
      const timer = window.setTimeout(() => { if (token === this.runToken) callback(); }, delay);
      this.timers.push(timer);
    }
    showStep(stepIndex) {
      const item = this.items[stepIndex];
      if (!item) return;
      this.index = stepIndex + 1;
      this.setStatus("running");
      this.shell.dataset.state = item.tone || "active";
      this.root.querySelectorAll("[data-progressive-step]").forEach((button, index) => button.setAttribute("aria-pressed", String(index === stepIndex)));
      this.detail.querySelector("small").textContent = `RUNNING · ${this.index} / ${this.items.length}`;
      this.detail.querySelector("h2").textContent = this.config.type === "timeline" ? item.title : `LINE ${String(this.index).padStart(2, "0")}`;
      this.detail.querySelector("p").textContent = this.config.type === "timeline" ? item.detail : item.explanation;
      if (this.index < this.items.length) {
        this.nextButton.textContent = this.config.type === "timeline" ? "다음 사건" : "다음 줄";
      }
      if (this.index >= this.items.length) this.complete();
    }
    complete() {
      this.clearTimers();
      this.setStatus("complete");
      this.shell.dataset.state = "complete";
      this.detail.querySelector("small").textContent = `COMPLETE · ${this.items.length} / ${this.items.length}`;
      this.nextButton.disabled = false;
      this.nextButton.textContent = "처음으로";
      this.context.announce?.("장면이 완료됐습니다");
    }
    start() {
      this.reset();
      this.setStatus("running");
      this.nextButton.disabled = true;
      const token = ++this.runToken;
      const interval = this.reducedMotion ? 45 : 1250;
      this.items.forEach((_, index) => this.schedule(() => this.showStep(index), index * interval + (this.reducedMotion ? 10 : 180), token));
    }
    advance() {
      if (this.status === "complete") { this.reset(); return; }
      this.showStep(this.index);
    }
    skip() {
      this.cancel();
      while (this.index < this.items.length) this.showStep(this.index);
      this.complete();
    }
    replay(autoplay = false) { this.reset(); if (autoplay) this.start(); }
    reset() {
      this.cancel();
      this.index = 0;
      this.setStatus("ready");
      this.render();
    }
    cancel() {
      this.runToken += 1;
      this.clearTimers();
      if (this.nextButton) this.nextButton.disabled = false;
    }
  }

  window.InteractiveSlideScenes = {
    create(root, config, context = {}) {
      if (!root || !config) return null;
      if (config.type === "sequence") return new SequenceScene(root, config, context);
      if (["timeline", "code-walkthrough"].includes(config.type)) return new ProgressiveScene(root, config, context);
      if (["steps", "comparison", "choice", "range", "diagram", "before-after"].includes(config.type)) return new InteractionScene(root, config, context);
      throw new Error(`지원하지 않는 scene type: ${config.type}`);
    }
  };
})();
