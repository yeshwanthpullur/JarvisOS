# Goal Intelligence

Goal Intelligence gives JARVIS practical goal understanding without duplicating Task Intelligence.

## Purpose

It helps JARVIS clarify vague intentions, evaluate whether a goal is actionable, decompose work into meaningful milestones, interpret progress from evidence, detect blockers and conflicts, and recommend grounded next steps.

## Authority Boundaries

- Executive JARVIS remains the decision authority.
- Task Intelligence remains the authoritative store for goals, milestones, tasks, and progress state.
- Context Intelligence remains responsible for what is currently active.
- Personal Intelligence remains responsible for durable user-specific context.

## What It Does

- Clarifies goals only when key information is missing
- Evaluates goal quality, feasibility, and review status
- Proposes milestones and goal-supporting tasks
- Interprets progress from authoritative evidence
- Detects blockers, risks, and conflicts
- Recommends a grounded next meaningful step
- Explains how tasks and workflows support a goal

## What It Does Not Do

- It does not create a second goal database
- It does not override Task Intelligence state
- It does not execute workflows or tasks
- It does not make provider calls
- It does not treat activity as completion

## Integration Flow

User request -> Conversation Engine -> Context Intelligence -> Goal Intelligence -> Task Intelligence / Workflow / Retrieval / Personal evidence -> Executive JARVIS -> Reasoning -> Execution path

## Completion

Goal completion is evidence-based. A goal is only considered complete when its success criteria are satisfied or the user explicitly confirms completion through the existing authoritative path.
