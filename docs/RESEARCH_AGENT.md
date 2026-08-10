# Research Agent

## Batch 2 Integration

Research planning may reference approved document evidence, read-only browser source policy, and advanced-provider comparisons. It does not gain autonomous browsing, hidden ingestion, fabricated citations, or external APIs.

Updated: 2026-08-10

JARVIS OS now includes a local-first Research Agent foundation for bounded research planning and evidence summaries.

## What It Can Do

- Normalize a research question.
- Classify the research intent.
- Build a bounded research plan.
- Describe the source policy that would be used.
- Produce a bounded summary when evidence is supplied.
- Record bounded metadata for recent research requests.
- Route research intent through Prime Agent without executing side effects.
- Declare advisory local reasoning capability through Model Router.
- Expose research planning and source-policy skills through Skill Registry.

## What It Cannot Do Yet

- It does not act as a fully autonomous internet researcher.
- It does not bypass the existing read-only web boundary.
- It does not log into websites.
- It does not submit forms.
- It does not bypass paywalls.
- It does not silently store research into Persistent Memory.
- It does not call external search APIs or claim that unavailable evidence was retrieved.

## Safety and Source Policy

- Unsafe requests are blocked.
- Private-person targeting is blocked.
- Source handling stays bounded and read-only.
- Evidence must be tied to a source reference when available.
- Claims without evidence are labeled honestly.
- Medical, legal, financial, safety-critical engineering, robotics, drone, and chemical topics stay high-level, identify uncertainty, and require confirmation before any action-oriented workflow.
- Runtime history under ignored `data/research/` stores IDs, intent, status, evidence counts, and timestamps only. It stores no full query or source content.

## Configuration

- `research.enabled = true`
- `research.default_depth = standard`
- `research.max_plan_steps = 5`
- `research.max_evidence_items = 5`
- `research.max_snippet_chars = 320`
- `research.max_summary_chars = 1200`
- `research.allow_web_read_only = true`
- `research.allow_external_search_api = false`
- `research.save_history = true`
- `research.local_only = true`
- `research.require_citations_for_web_claims = true`

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
