# Design-plan production contract

`design-plan.json` is the implementation manifest between an approved production proposal and final HTML, CSS and JavaScript. It makes visual and interaction choices inspectable before production and prevents the generated deck from drifting away from the approved scope.

The production proposal remains the canonical scope record. A design plan may clarify composition and implementation, but it cannot add slides, change the selected mode or reinterpret approval.

## Proposal binding

Create the plan from `templates/design-plan.json` only after the proposal passes its approval gate. Bind these exact values:

- approved proposal version
- proposal title
- locked `demo` or `experience` mode
- lowercase SHA-256 of the complete proposal file
- every proposal slide whose row status is `approved`

Do not include `remove` or `defer` rows in the design plan. If the proposal changes after the plan is created, its hash becomes stale and the plan must be regenerated or revised.

## Art direction and slide families

Define one coherent art direction before assigning layouts. Record:

- editorial premise
- display, body and numeral typography
- background, foreground and accent palette
- image treatment
- grid and geometry
- motion language
- one icon family

Define a small set of slide families with purposeful differences in composition, visual anchor and density. A family is not a generic card grid. Adjacent slides may share a family when the narrative requires continuity, but the complete deck should still have recognizable rhythm in thumbnail view.

## Slide production decisions

Each approved slide must declare:

- purpose and working headline
- slide family, composition and dominant visual
- speaking time and content budget
- evidence boundary and source or asset IDs
- adopted or rejected interaction decision
- keyboard, reduced-motion and static-fallback behavior

Keep the working headline within its declared character budget and write for projection rather than document reading. Use source and asset IDs from the approved proposal; do not invent evidence to fill a composition.

## Interaction contract

For an adopted interaction:

- select a supported scene type other than `static`
- record at least two distinct benefits from `causality`, `temporal`, `decision`, `comparison` and `spatial`
- use `ready-running-complete` lifecycle in `demo` mode
- use `direct-manipulation-reset` lifecycle in `experience` mode
- provide a meaningful static fallback

For a rejected interaction, use `scene_type: static`, `lifecycle: none` and state why a static composition communicates better.

## Presentation chrome

Presentation panels and utilities remain outside slide content. The plan must keep them icon-only while requiring accessible names and tooltips. Use one SVG icon family and preserve visible focus and native keyboard behavior.

## Production gate

Set `plan_status` to `ready` only when the plan is complete, then run:

```text
python scripts/validate_design_plan.py design-plan.json --proposal production-proposal.md --require-ready
```

Do not start final production when the proposal is unapproved, the proposal hash is stale, approved slide IDs differ, the mode differs, or an adopted interaction lacks value, lifecycle or fallback evidence.
