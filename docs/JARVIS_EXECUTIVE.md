# Executive JARVIS Core

JARVIS is the permanent Executive Intelligence layer of JARVIS OS. It is not an agent. Every future request enters JARVIS first, then flows through intent detection, decision metadata, reasoning, retrieval planning, goal intelligence, task intelligence, research intelligence, personal intelligence, planning, workflow orchestration, dispatch, reflection, adaptive intelligence, existing managers, response building, and history.

JARVIS never talks directly to AI providers. Provider work must route through the existing Provider Router.

The Conversation Engine and Command Engine now provide the user-facing operating interface for Executive JARVIS. CLI input flows through conversation context, command parsing or request handling, and then into the Executive pipeline.

Personal Intelligence is advisory context that can be supplied to Executive JARVIS through existing memory and retrieval paths. It can improve personalization, but it cannot override the current explicit instruction or act as a separate decision layer.

Context Intelligence is the continuity layer supplied through the existing conversation path. It can provide the active objective, active work reference, continuation metadata, recent compatible context, and ambiguity status. Executive JARVIS remains the decision authority and does not treat low-confidence context as unquestionable truth.

Goal Intelligence sits between context and execution for goal-related requests. It clarifies goals, evaluates quality, interprets progress, and recommends grounded next steps, while Task Intelligence remains the authority for goal and milestone records.

Local AI is routed only through the Provider Router. Executive JARVIS may request local-only execution or model selection, but it never talks to local runtimes directly and it never treats local model output as authority.

Reflection is the post-execution counterpart to reasoning. It evaluates completed work, prepares learning metadata, and supports future reasoning improvements. It remains advisory only.

Adaptive Intelligence reviews reflection and learning metadata after execution. It prepares validated recommendations for Executive JARVIS, which remains the only authority that can approve adaptation.

## Responsibilities

- Receive requests
- Build execution context
- Identify intent
- Decide strategy
- Prepare plans
- Decide what information must be retrieved
- Create and coordinate workflows
- Dispatch to existing systems
- Coordinate memory, knowledge, tasks, plugins, tools, skills, departments, agents, and providers
- Compose responses
- Track metrics, health, diagnostics, history, and recovery metadata

## Workflow Boundary

JARVIS creates workflow definitions and hands execution to the Workflow Engine. The Workflow Engine manages workflow scheduling, checkpoints, recovery, and history. Provider execution inside a workflow must continue to flow through the Provider Execution Framework and Provider Router.

JARVIS also decides which information should be retrieved. The Retrieval Engine is responsible for precision lookup, ranking, and reference building across memory, knowledge, Obsidian, and historical sources.

## Current Limitations

This foundation contains architecture only. It does not implement AI calls, browser automation, desktop automation, voice, vision, internet automation, or autonomous execution.
