# Personal Intelligence

Personal Intelligence is the user-facing layer that helps JARVIS build and use a structured, evidence-based understanding of the user without duplicating storage.

## Purpose

It tracks durable personal facts, preferences, interests, working patterns, project references, and confidence-backed inferences when they are useful in future work.

## Boundaries

- Memory Engine stores the durable records.
- Retrieval Engine returns only relevant context.
- Conversation Engine can capture explicit statements and pass context forward.
- Executive JARVIS decides whether personal context should influence a request.
- Provider Router remains the only provider gateway.

## Evidence Model

Each personal item is stored with:

- Category
- Value
- Source type
- Source reference
- Confidence
- Explicit or inferred classification
- Confirmation history
- Contradiction metadata
- Active and superseded state

## User Control

The user can view, explain, update, confirm, reject, supersede, or forget personal information through the existing command and conversation paths.

## Privacy

Only personal information with likely future utility should be stored. Personal intelligence should prefer references and metadata over duplicate content whenever possible.
