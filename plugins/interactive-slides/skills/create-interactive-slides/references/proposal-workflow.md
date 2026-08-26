# Proposal-first production workflow

Do not begin final slide production from raw requirements. Convert the request into a reviewable production proposal, revise it with the user, and enter production only after explicit approval.

## State model

```text
intake -> analysis -> proposal -> review -> approved -> production -> qa -> delivered
```

The proposal is the canonical scope record. Update its version and revision history whenever feedback changes slide count, duration, assets, interactions, visual direction, delivery constraints or acceptance criteria.

## 1. Intake

Use the authoring intake contract first. Collect only missing information:

- required mode: `demo` or `experience`
- purpose, audience, venue, duration and delivery target
- requirements, exclusions and mandatory messages
- script, outline or source material when available
- brand assets, reference decks and visual constraints
- evidence, privacy, offline and integration constraints

A script is optional. If absent, mark speaking-time and slide-density estimates as lower confidence and identify the outline decisions needed from the user.

## 2. Analysis

Analyze before proposing slides:

- segment the script or source into opening, claims, evidence, transitions, demonstration moments and closing
- identify duplicated, missing or unsupported claims
- estimate speaking time and state the pacing assumption used
- identify content that needs an image, chart, diagram, code view, simulation or live integration
- distinguish supplied facts from interpretation and reconstruction
- identify questions that block a credible proposal
- select interaction only where it improves explanation or audience action

Do not invent facts, metrics, sources, assets or product behavior to make the proposal appear complete.

## 3. Production scope estimate

Create a versioned proposal from `templates/production-proposal.md`. It must contain:

- one-sentence outcome and narrative structure
- estimated slide count and presentation duration
- slide-by-slide purpose, content, composition, interaction, source, asset and speaking-time plan
- visual direction and slide-family plan
- interaction count and lifecycle complexity
- asset, source and integration inventory
- delivery, accessibility and fallback requirements
- risks, assumptions, blocking questions and confidence
- explicit acceptance criteria

Use an integer slide count in the canonical proposal. Discuss alternatives as scenarios rather than encoding an ambiguous range.

### Relative effort model

Use effort points only to compare scope, never as guaranteed hours:

- static statement, quote or section slide: 1
- evidence, chart, comparison or image-led composition: 2
- diagram, timeline or direct-manipulation scene: 3
- blocking demo scene with replay, skip and fallback: 5
- live external integration or custom data transformation: 8 plus explicit risk

Estimate monetary cost only when the user supplies a rate card, currency and pricing rules. Otherwise report production scope, effort points and uncertainty without inventing a price.

## 4. Review and revision

Accept feedback in natural language or with `templates/proposal-feedback.md`. Classify each response as:

- approve
- revise
- remove
- merge
- split
- defer

Return a new proposal version with a concise change summary and updated impact on slide count, duration, assets, effort and risk. Preserve the prior version; do not silently overwrite decisions in the revision history.

The user may approve individual slides while others remain under review. The overall proposal remains `review` until every blocking decision is resolved.

## 5. Approval gate

Before production:

1. Set `proposal_status: approved` only after an explicit user approval.
2. Record `approved_by`, `approved_at` and `blocking_questions: 0`.
3. Run `validate_production_proposal.py --require-approved` when execution is available.
4. Do not create the final HTML, CSS, JavaScript or production assets if the gate fails.

Storyboards, wireframes and small design-direction samples are review artifacts, not final production. Label them accordingly.

## 6. Production and change control

Build against the approved slide rows and acceptance criteria. If a request during production changes scope:

- record the change
- show its impact on count, duration, assets, effort and risk
- return the proposal to `review`
- obtain approval for the revised version before continuing the affected work

Minor corrections that do not change scope may remain in production but still belong in the revision history.

## 7. Proposal-to-delivery QA

At delivery, reconcile every approved slide row with the generated deck. Report implemented, changed, deferred and missing items. A technically valid deck is not complete when it diverges from the approved proposal without a recorded decision.
