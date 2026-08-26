# Authoring intake and mode lock

Choose the presentation contract before writing the storyboard or generating UI.

## Required preflight

Collect these inputs in the first prompt when they are not already supplied:

- purpose and one-sentence audience outcome
- audience, venue, duration and expected device
- source material and required evidence boundaries
- presentation mode: `demo` or `experience`
- brand assets or one visual direction
- offline, hosting and browser constraints

Ask only for missing decisions. If mode is missing, ask one compact choice question before producing slides:

- `demo`: presenter-controlled sequence, deterministic timing, replay and skip
- `experience`: audience-controlled exploration, direct manipulation and reset

Do not generate both modes speculatively. Do not expose a mode switch in the delivered presentation. A hybrid deck is allowed only when the user explicitly requests it; define the mode per slide during storyboarding instead of adding a global runtime toggle.

## Build contract

Write the selected mode into the brief and storyboard. Set it declaratively on the generated document:

```html
<html lang="ko" data-presentation-mode="demo">
```

Use `experience` for an experience deck. The starter reads this value once at startup and removes the authoring-only mode control from the presentation chrome.

### Demo mode

- Keep slide progression presenter-controlled.
- Blocking scenes must have ready, running and complete states.
- Provide replay and skip without leaving timers or stale callbacks.
- Keep essential meaning visible in the static fallback.
- Put timing and speaking cues in presenter notes.

### Experience mode

- Make the primary interaction directly visible and self-explanatory.
- Provide reset and a deterministic initial state.
- Do not require autoplay or hidden keyboard knowledge.
- Preserve slide navigation while the audience explores.
- Ensure touch targets and mobile layout remain usable.

## Acceptance check

Reject the generated deck when the brief, storyboard and document mode disagree, or when a runtime mode toggle remains visible without an explicit hybrid requirement.
