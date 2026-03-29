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