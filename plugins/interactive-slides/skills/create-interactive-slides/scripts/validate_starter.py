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
    runtime = files["presentation.js"]
    scenes = files["scenes.js"]
    checks = {
        "scripts load in dependency order": index.find('src="deck.js"') < index.find('src="scenes.js"') < index.find('src="presentation.js"'),
        "deck controls are present": all(f'id="{control}"' in index for control in ("outlineBtn", "replayBtn", "zoomOut", "zoomIn", "fitBtn", "fullBtn", "progressTrack")),
        "speaker notes are present": 'id="speakerNotes"' in index,
        "styles honor reduced motion": "prefers-reduced-motion" in files["styles.css"],
        "styles define 16 by 9 stage": "--stage-width: 1600px" in files["styles.css"] and "--stage-height: 900px" in files["styles.css"],
        "deck exports data": "window.INTERACTIVE_DECK" in files["deck.js"],
        "deck includes evidence boundaries": all(marker in files["deck.js"] for marker in ("verified", "analysis", "simulation", "SYNTHETIC TELEMETRY")),
        "scene factory is exported": "window.InteractiveSlideScenes" in scenes,
        "expanded scene recipes are implemented": all(f'"{scene_type}"' in scenes for scene_type in ("timeline", "diagram", "code-walkthrough", "before-after")),
        "expanded scene recipes have starter examples": all(f'type: "{scene_type}"' in files["deck.js"] for scene_type in ("timeline", "diagram", "code-walkthrough", "before-after")),
        "sequence owns lifecycle": all(marker in scenes for marker in ('"ready"', '"running"', '"complete"', "runToken", "clearTimers")),
        "deck destroys scenes": "state.scene?.destroy()" in runtime,
        "navigation cancels scenes": "state.scene?.cancel()" in runtime,
        "demo intercepts forward navigation": 'state.mode === "demo" && state.scene?.blocksAdvance' in runtime,
        "runtime supports experience": '"experience"' in runtime,
        "runtime supports demo": '"demo"' in runtime,
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
