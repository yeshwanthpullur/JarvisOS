# Reflection Engine

The Reflection Engine evaluates completed work after execution. It does not make decisions before execution and it does not replace Executive JARVIS.

## Purpose

- Compare expected outcomes with actual outcomes
- Measure confidence accuracy
- Identify assumptions, misses, and inefficiencies
- Generate improvement metadata for future reasoning

## Architecture

- `ReflectionManager` coordinates reflection lifecycle, history, metrics, diagnostics, registry, and validation.
- `ReflectionEngine` performs the analysis pipeline.
- `ReflectionAnalyzer` compares expected and actual results.
- `ReflectionLearning` captures learning metadata.
- `ReflectionPatterns` stores reusable pattern metadata.
- `ReflectionConfidence` evaluates confidence drift.
- `ReflectionImprovement` produces ranked recommendations.
- `ReflectionFeedback` packages advisory output for Executive JARVIS.

## Boundaries

- Reflection never bypasses Executive JARVIS
- Reflection never bypasses Provider Router
- Reflection does not write directly to memory or knowledge stores
- Reflection only prepares metadata for later storage or review

