# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

This implementation includes a complete scheduling pipeline and owner-facing feedback designed for day-to-day pet care planning.

- Owner and pet profile management:
	- Supports one owner with multiple pets.
	- Keeps per-pet health context, care tasks, medications, and appointments.

- Task modeling with real scheduling constraints:
	- Each task can include duration, priority, preferred time window, due time, recurrence, and owner-required flag.
	- Tasks are validated against pet ownership and protected from duplicate task IDs.

- Urgency-first task ranking algorithm:
	- Tasks are scored by weighted priority, proximity to due time, recurrence type, and owner involvement.
	- Scheduler sorts tasks from highest to lowest urgency score before assigning time slots.

- Feasibility filtering before scheduling:
	- Automatically filters out completed tasks.
	- Excludes tasks that cannot fit available minutes.
	- Excludes tasks whose preferred windows do not overlap the selected day window.

- Time-window-aware timestamp assignment:
	- Converts day window and preferred windows into real datetime bounds.
	- Assigns start/end timestamps in chronological order using a moving cursor.
	- Skips tasks that cannot fully fit within valid time bounds.

- Conflict-safe schedule resolution:
	- Enforces no overlap between scheduled entries.
	- Enforces daily minute budget using owner availability and scheduler max cap.
	- Returns both scheduled entries and dropped entries for feedback.

- Conflict warnings and professional schedule feedback in Streamlit:
	- Displays a sorted feasible-task table with urgency scores.
	- Displays a filtered-task table with skip reasons.
	- Displays a "PawPal conflict alert" warning with held tasks when overlap or time-cap conflicts occur.
	- Displays final scheduled tasks in a clean table format.

- Recurrence automation on task completion:
	- Completing a daily or weekly task auto-creates the next follow-up task instance.
	- Follow-up tasks retain key properties and receive a rolled due date and unique ID.

- Plan persistence and explainability:
	- Stores generated plans by date for later retrieval.
	- Produces a plain-language explanation of what was scheduled, when, and for which pet.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

Current tests cover core scheduling and task behaviors, including:

- Marking a task as completed updates its completion state.
- Adding a task to a pet increases that pet's task count.
- Generated schedule entries are returned in chronological order (without overlaps).
- Completing a daily recurring task creates a follow-up task due the next day.
- "Confidence Level": 4/5