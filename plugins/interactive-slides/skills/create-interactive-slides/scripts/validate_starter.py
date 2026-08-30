#!/usr/bin/env python3
"""Validate the dependency-free interactive slide starter contract."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "assets" / "starter"
REQUIRED = ("index.html", "styles.css", "deck.js", "scenes.js", "presentation.js")


def main() -> int:
    failures: list[str] = []
    files: dict[str, str] = {}
    for name in REQUIRED:
        path = STARTER / name
        if not path.is_file():
            failures.append(f"missing starter file: {name}")
            continue
        files[name] = path.read_text(encoding="utf-8")
    if failures:
        print("\n".join(failures))
        return 1

    index = files["index.html"]
    deck = files["deck.js"]
    runtime = files["presentation.js"]
    scenes = files["scenes.js"]
    styles = files["styles.css"]
    script_positions = [
        index.find('src="deck.js"'),
        index.find('src="scenes.js"'),
        index.find('src="presentation.js"'),
    ]
    opening_markers = (
        "설명을 시연으로 바꾸는 발표",
        "DEMO-DRIVEN PRESENTATION",
        "시연형 슬라이드는 다음 장으로 가기 전에 현재 장면을 완성한다.",
        "슬라이드 이동과 장면 재생을 분리하면 발표자는 같은 흐름을 안정적으로 반복할 수 있습니다.",
        "Deck Controller는 이동을 관리합니다.",
        "Scene Controller는 재생 상태를 관리합니다.",
        "설계 원칙",
        "Interactive Slides starter · architecture contract",
    )
    checks = {
        "scripts load in dependency order": (
            all(position >= 0 for position in script_positions)
            and script_positions == sorted(script_positions)
        ),
        "deck controls are present": all(f'id="{control}"' in index for control in ("outlineBtn", "replayBtn", "zoomOut", "zoomIn", "fitBtn", "fullBtn", "progressTrack")),
        "speaker notes are present": 'id="speakerNotes"' in index,
        "styles honor reduced motion": "prefers-reduced-motion" in styles,
        "styles define 16 by 9 stage": "--stage-width: 1600px" in styles and "--stage-height: 900px" in styles,
        "mobile layout reflows instead of scaling": all(marker in styles for marker in ("@media (max-width: 720px)", "height: auto", "transform: none !important", "overflow: visible")),
        "deck exports data": "window.INTERACTIVE_DECK" in deck,
        "deck includes evidence boundaries": all(marker in deck for marker in ("verified", "analysis", "simulation", "SYNTHETIC TELEMETRY")),
        "scene factory is exported": "window.InteractiveSlideScenes" in scenes,
        "expanded scene recipes are implemented": all(f'"{scene_type}"' in scenes for scene_type in ("timeline", "diagram", "code-walkthrough", "before-after")),
        "expanded scene recipes have starter examples": all(f'type: "{scene_type}"' in deck for scene_type in ("timeline", "diagram", "code-walkthrough", "before-after")),
        "sequence owns lifecycle": all(marker in scenes for marker in ('"ready"', '"running"', '"complete"', "runToken", "clearTimers")),
        "sequence completion restores reset control": 'this.nextButton.textContent = "처음으로";' in scenes and "this.nextButton.disabled = false;" in scenes,
        "progressive revisit restores action label": 'this.index < this.items.length' in scenes and '"다음 사건" : "다음 줄"' in scenes,
        "deck destroys scenes": "state.scene?.destroy()" in runtime,
        "navigation cancels scenes": "state.scene?.cancel()" in runtime,
        "demo intercepts forward navigation": 'state.mode === "demo" && state.scene?.blocksAdvance' in runtime,
        "runtime supports experience": '"experience"' in runtime,
        "runtime supports demo": '"demo"' in runtime,
        "controls retain native keyboard behavior": "if (onControl) return;" in runtime,
        "touch gestures ignore interactive controls": all(marker in runtime for marker in ("touchStartedOnControl", "startedOnControl")),
        "locked authoring mode has no runtime shortcut": 'event.key.toLowerCase() === "m"' not in runtime,
        "starter keeps a static first-slide fallback": all(marker in index for marker in ("static-fallback-wrap", "has-static-fallback", 'class="slide static-fallback"')),
        "static fallback matches the opening slide": all(marker in index and marker in deck for marker in opening_markers),
        "runtime progressively replaces static fallback": all(marker in runtime for marker in ('classList.remove("static-fallback-wrap")', 'classList.remove("has-static-fallback")')),
        "unsupported scenes preserve configured fallback": "throw new Error" in scenes and "지원하지 않는 scene type" in scenes,
        "runtime avoids dynamic evaluation": not any(marker in scenes + runtime for marker in ("eval(", "new Function")),
        "starter is offline": not any("https://" in text or "http://" in text for text in files.values()),
        "starter has no placeholders": not any("[TODO:" in text for text in files.values()),
    }
    failures.extend(label for label, passed in checks.items() if not passed)
    if failures:
        print("INTERACTIVE SLIDES STARTER FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("INTERACTIVE SLIDES STARTER PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
