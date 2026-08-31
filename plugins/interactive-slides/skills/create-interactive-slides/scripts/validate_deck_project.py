#!/usr/bin/env python3
"""Validate an Interactive Slides output directory without third-party packages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_FILES = ("index.html", "styles.css", "deck.js", "scenes.js", "presentation.js")
SLIDE_ID = re.compile(r"\bid\s*:\s*[\"']([a-z0-9]+(?:-[a-z0-9]+)*)[\"']")
REMOTE_ASSET_PATTERNS = (
    re.compile(
        r"<(?:script|img|source|video|audio|iframe|embed)\b[^>]*"
        r"\b(?:src|srcset)\s*=\s*(?:[\"'][^\"']*https?://|[^\s>\"']*https?://)",
        re.IGNORECASE,
    ),
    re.compile(
        r"<link\b[^>]*\bhref\s*=\s*(?:[\"'][^\"']*https?://|[^\s>\"']*https?://)",
        re.IGNORECASE,
    ),
    re.compile(
        r"<object\b[^>]*\bdata\s*=\s*(?:[\"'][^\"']*https?://|[^\s>\"']*https?://)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:url\(\s*[\"']?|@import\s+[\"']?)https?://", re.IGNORECASE),
    re.compile(r"\bfetch\s*\(\s*[\"'`]https?://", re.IGNORECASE),
    re.compile(r"\bimport\s*(?:\(\s*)?[\"'`]https?://", re.IGNORECASE),
)


def count_remote_assets(texts: dict[str, str]) -> int:
    return sum(
        len(pattern.findall(text))
        for text in texts.values()
        for pattern in REMOTE_ASSET_PATTERNS
    )


def extract_slide_blocks(deck: str) -> list[str]:
    match = re.search(r"\bslides\s*:\s*\[", deck)
    if match is None:
        return []
    blocks: list[str] = []
    bracket_depth = 0
    brace_depth = 0
    block_start: int | None = None
    quote: str | None = None
    escaped = False
    for index in range(match.end() - 1, len(deck)):
        character = deck[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"\"", "'", "`"}:
            quote = character
            continue
        if character == "[":
            bracket_depth += 1
        elif character == "]":
            bracket_depth -= 1
            if bracket_depth == 0:
                break
        elif character == "{":
            if bracket_depth == 1 and brace_depth == 0:
                block_start = index
            brace_depth += 1
        elif character == "}":
            brace_depth -= 1
            if bracket_depth == 1 and brace_depth == 0 and block_start is not None:
                blocks.append(deck[block_start : index + 1])
                block_start = None
    return blocks


def validate(project: Path, *, allow_remote_assets: bool) -> tuple[list[str], list[str], dict[str, int]]:
    failures: list[str] = []
    warnings: list[str] = []
    texts: dict[str, str] = {}
    for name in REQUIRED_FILES:
        path = project / name
        if not path.is_file():
            failures.append(f"missing required file: {name}")
            continue
        texts[name] = path.read_text(encoding="utf-8")
    if failures:
        return failures, warnings, {"slides": 0, "remote_urls": 0}

    index = texts["index.html"]
    styles = texts["styles.css"]
    deck = texts["deck.js"]
    scenes = texts["scenes.js"]
    runtime = texts["presentation.js"]
    combined = "\n".join(texts.values())
    script_positions = [
        index.find('src="deck.js"'),
        index.find('src="scenes.js"'),
        index.find('src="presentation.js"'),
    ]

    checks = {
        "scripts must load deck, scenes, presentation in order": (
            all(position >= 0 for position in script_positions)
            and script_positions == sorted(script_positions)
        ),
        "index must expose semantic stage": 'id="stage"' in index and 'aria-live="polite"' in index,
        "index must expose outline and progress": 'id="outline"' in index and 'id="progressTrack"' in index,
        "index must expose replay and fullscreen": 'id="replayBtn"' in index and 'id="fullBtn"' in index,
        "styles must support reduced motion": "prefers-reduced-motion" in styles,
        "deck must export INTERACTIVE_DECK": "window.INTERACTIVE_DECK" in deck,
        "deck must include speaker notes": "notes:" in deck,
        "deck must include source boundaries": "sources:" in deck and "evidence:" in deck,
        "scene runtime must expose factory": "window.InteractiveSlideScenes" in scenes,
        "scene runtime must implement expanded recipes": all(f'"{scene_type}"' in scenes for scene_type in ("timeline", "diagram", "code-walkthrough", "before-after")),
        "scene runtime must track lifecycle": all(marker in scenes for marker in ('"ready"', '"running"', '"complete"')),
        "scene runtime must invalidate stale runs": "runToken" in scenes and "clearTimers" in scenes,
        "deck runtime must destroy scenes": "state.scene?.destroy()" in runtime,
        "deck runtime must cancel scenes": "state.scene?.cancel()" in runtime,
        "deck runtime must support both modes": '"experience"' in runtime and '"demo"' in runtime,
        "deck runtime must enforce locked authoring mode": all(
            marker in runtime
            for marker in (
                "deck.meta.modeLocked === true",
                "!modeLocked &&",
                "if (modeLocked) return",
                "elements.mode.hidden = true",
                'event.key.toLowerCase() === "m" && !modeLocked',
            )
        ),
        "deck runtime must render scene fallback": "slide.fallback || slide.summary" in runtime and "scene-fallback" in runtime,
        "dynamic code evaluation is forbidden": "eval(" not in scenes + runtime and "new Function" not in scenes + runtime,
        "unfinished placeholders are forbidden": "[TODO:" not in combined and "Lorem ipsum" not in combined,
    }
    failures.extend(label for label, passed in checks.items() if not passed)

    slide_blocks = extract_slide_blocks(deck)
    slide_ids: list[str] = []
    for index, block in enumerate(slide_blocks, 1):
        match = SLIDE_ID.search(block)
        if match is None:
            failures.append(f"slide {index} needs a lower-kebab-case id")
        else:
            slide_ids.append(match.group(1))
    if not slide_blocks:
        failures.append("deck must define at least one lower-kebab-case slide id")
    if len(slide_ids) != len(set(slide_ids)):
        failures.append("deck contains duplicate slide ids")

    remote_count = count_remote_assets(texts)
    if remote_count and not allow_remote_assets:
        failures.append(f"remote URLs require --allow-remote-assets: {remote_count} found")
    elif remote_count:
        warnings.append(f"remote assets allowed explicitly: {remote_count} URLs")

    if "SYNTHETIC TELEMETRY" not in deck and "sequence" in deck:
        warnings.append("sequence scene has no SYNTHETIC TELEMETRY marker; confirm whether its data is factual")
    if "fallback" not in deck.lower():
        warnings.append("deck data does not name a fallback; confirm static summaries cover scene failure")

    return failures, warnings, {"slides": len(slide_blocks), "remote_urls": remote_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing index.html and deck runtime files")
    parser.add_argument("--allow-remote-assets", action="store_true", help="Allow remote asset loads and report them as warnings")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable result")
    args = parser.parse_args()

    project = args.project.resolve()
    failures, warnings, metrics = validate(project, allow_remote_assets=args.allow_remote_assets)
    payload = {
        "status": "failed" if failures else "passed",
        "project": str(project),
        "metrics": metrics,
        "warnings": warnings,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"INTERACTIVE DECK VALIDATION {payload['status'].upper()}: {metrics['slides']} slides")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for failure in failures:
            print(f"ERROR: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
