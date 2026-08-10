# Research Agent

Updated: 2026-08-10

JARVIS OS now includes a local-first Research Agent foundation for bounded research planning and evidence summaries.

## What It Can Do

- Normalize a research question.
- Classify the research intent.
- Build a bounded research plan.
- Describe the source policy that would be used.
- Produce a bounded summary when evidence is supplied.
- Record bounded metadata for recent research requests.

## What It Cannot Do Yet

- It does not act as a fully autonomous internet researcher.
- It does not bypass the existing read-only web boundary.
- It does not log into websites.
- It does not submit forms.
- It does not bypass paywalls.
- It does not silently store research into Persistent Memory.

## Safety and Source Policy

- Unsafe requests are blocked.
- Private-person targeting is blocked.
- Source handling stays bounded and read-only.
- Evidence must be tied to a source reference when available.
- Claims without evidence are labeled honestly.

## Commands

- `research status`
- `research help`
- `research plan <query>`
- `research safety <query>`
- `research sources <query>`
- `research summarize <query>`
- `research evidence <research_id>`
- `research show <research_id>`
- `research history`

Research remains a foundation milestone, not a complete autonomous research product.
