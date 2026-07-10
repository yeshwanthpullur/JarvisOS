# Task Intelligence

Task Intelligence is the project-management layer above the existing Task Engine. The legacy Task Engine remains the persistence and lifecycle surface for individual tasks. Task Intelligence adds higher-level structure for projects, goals, milestones, priorities, schedules, progress, dashboards, and reporting.

## Boundary

- Task Engine: owns task records, queueing, history, and lifecycle primitives.
- Task Intelligence: owns project organization and planning metadata.
- Executive JARVIS: decides what should happen.
- Workflow Engine: coordinates execution.

## Core Components

- `ProjectManager`
- `GoalManager`
- `MilestoneManager`
- `DependencyManager`
- `PriorityEngine`
- `ScheduleEngine`
- `ProgressTracker`
- `TaskDashboard`
- `TaskTemplates`
- `TaskMetrics`
- `TaskDiagnostics`

## Integration Rules

- Do not duplicate task persistence.
- Do not bypass the Workflow Engine.
- Do not bypass Executive JARVIS.
- Keep behavior configuration-driven.
- Extend through interfaces instead of rewriting the base Task Engine.
