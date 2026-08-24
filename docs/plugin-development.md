# Plugin Development Guide

## Plugin goals

A plugin should provide a focused capability with explicit behavior, evaluation, and ownership boundaries.

## Required components

```text
plugin-name/
├── .codex-plugin/
│   ├── plugin.json
│   └── quality-gates.json
└── skills/
    └── skill-name/
        ├── SKILL.md
        ├── references/
        ├── scripts/
        └── evals/
```

## Development rules

### 1. Define capability

Document what the plugin can do and what it intentionally does not do.

### 2. Add evaluation cases

Every important behavior should have regression examples.

### 3. Keep contracts stable

Breaking changes require version changes and migration notes.

## Review checklist

- Manifest is valid.
- Skills have clear responsibilities.
- Evaluation cases cover expected behavior.
- Quality gates pass.
