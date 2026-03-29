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


### Smarter Scheduling 

Tasks now spawns a new successor from daily and weekly tasks, inheriting certain traits but making task id, create_at, and due_date. 

Schedular has filter tasks feature, sorting feature, conflict detection feature, recurrence wiring, and demo coverage to help with handling tasks and making a demo for the system. 

### Testing PawPal+

I used python -m pytest to run all 17 tests for pawpal_system.py. Those tests cover over the task system, making sure they are working correctly like show as pending, not being skipped over, and being set as completed. There are other tests regarding adding tasks for each pet, setting the tasks in chronological order, recurring tasks such as daily and weekly tasks, and finally testing tasks that conflict with each other. 

Base on my observation of the system and testing it, I would say my confidence level in the system is four stars in the system's reliability based on my test results. While they have had all passed, there was still some struggles in the initial tests Claude has given to me and I had to fix the _ALLOWED_TRANSITIONS section for all of the tests to pass.

### PawPal — Feature List
# Task Management

Status lifecycle — Tasks move through a strict state machine: PENDING → IN_PROGRESS → DONE, with an optional SKIPPED exit at any non-terminal state. Invalid transitions raise a RuntimeError via a centralised _transition() guard table.
Field validation — Duration (must be > 0) and priority (must be 1–5) are enforced at construction via __post_init__ and re-validated on every edit() call.
Due date support — Tasks carry an optional due_date field used to anchor recurrence scheduling and overdue detection to a specific calendar date.

# Recurrence & Scheduling

Daily and weekly recurrence — When a DAILY or WEEKLY task is marked done, _spawn_next_occurrence() automatically creates a successor task. The new due date is anchored to the original due date plus a fixed delta (timedelta(days=1) or timedelta(weeks=1)), preventing schedule drift from late completions.
Priority-based heap sort — _priority_sort() uses Python's heapq to sort tasks by descending priority, then by earliest scheduled_time, then by shortest duration. Sort keys are pre-computed and cached in _sort_key so re-sorting is O(n log n) without recalculating per comparison.
Time-of-day sorting — sort_by_time() returns the schedule ordered strictly by scheduled_time (HH:MM ascending). Tasks without a scheduled time are placed at the end using a sentinel value ("99:99").
Overdue detection — overdue() compares each pending task's datetime.combine(due_date, scheduled_time) against a reference timestamp (defaults to datetime.now()), returning only tasks that are genuinely past due.

# Conflict Detection

Same-time conflict detection — detect_conflicts() uses an O(n) bucket pass: tasks are grouped by their "HH:MM" string into a dict, then any bucket with 2+ tasks emits one ConflictResult per unique pair via an inner loop. This avoids a full O(n²) pairwise scan.
Cross-pet vs. same-pet classification — Each ConflictResult records whether the conflicting tasks belong to the same pet or different pets, enabling targeted reporting.
Safe conflict warnings — warn_conflicts() wraps detect_conflicts() in a try/except so detection failures surface as a warning string rather than crashing the caller. Returns an empty list when the schedule is clean, making it safe to use as a boolean gate (if scheduler.warn_conflicts()).
Conflict report printing — print_conflicts() produces a formatted stdout report, separating same-pet and cross-pet conflicts into labelled sections.

# Filtering & Querying

Predicate-based filtering — filter(predicate) accepts any Callable[[Task], bool], making it the generic backbone for all other filter helpers.
Combined status + pet filter — filter_tasks(status, pet_name) supports filtering by completion status and pet name simultaneously, using a pre-built task ID set for the pet lookup rather than repeated linear scans.
Convenience filters — by_status(), by_priority(), and by_frequency() are thin wrappers over filter() for the most common query patterns.

# Pet & Owner Management

O(1) task lookup — Pet stores tasks in a dict[task_id → Task] rather than a list, making get_task(), remove_task(), and duplicate detection all O(1).
Cached completion counter — Pet._done_count is maintained incrementally on every add_task(), remove_task(), and reset_recurring_tasks() call, so completion_rate is O(1) rather than O(n).
Name index on Owner — Owner._pets_by_name is a secondary dict[name → list[Pet]] updated on every add_pet() and remove_pet(), making find_pets(name=...) an O(1) lookup rather than a full scan.
Generator-based task iteration — Owner.iter_tasks() yields (Pet, Task) pairs lazily via a Generator, avoiding the cost of materialising the full list when only iteration is needed.
Selective recurring reset — reset_all_recurring(frequency=...) accepts an optional frequency filter, so only DAILY or only WEEKLY tasks can be reset independently without touching the other group.

# Schedule History

Capped snapshot history — Before every generate_schedule() call, the previous schedule is saved as a timestamped snapshot in a deque(maxlen=20). The cap prevents unbounded memory growth across many regenerations.
O(1) schedule index — Scheduler._schedule_index is a dict[task_id → Task] rebuilt on every generate_schedule(), making _find_in_schedule() an O(1) lookup instead of a linear scan through self.schedule.

<a href="C:\Users\aaske\Downloads\ai110-module2show-pawpal-starteruml_final.png" target="_blank"><img src='C:\Users\aaske\Downloads\ai110-module2show-pawpal-starteruml_final.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.