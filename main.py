"""
main.py
Entry point for the PawPal pet care system.
Run with: python main.py
Run smoke test with: python main.py --smoke
"""

from datetime import time

from pawpal_system import Frequency, Owner, Pet, Scheduler, Status, Task

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIVIDER      = "═" * 56
THIN_DIVIDER = "─" * 56

STATUS_ICON = {
    "pending":     "○",
    "in_progress": "◑",
    "done":        "●",
    "skipped":     "✕",
}

def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def print_schedule(scheduler: Scheduler) -> None:
    section("🐾  PawPal — Today's Schedule")

    if not scheduler.schedule:
        print("  No tasks scheduled.")
        return

    # Group tasks by pet name for a cleaner printout
    grouped: dict[str, list[Task]] = {}
    for pet in scheduler.owner.all_pets():
        tasks = [t for t in scheduler.schedule if t in pet.all_tasks()]
        if tasks:
            grouped[pet.name] = tasks

    for pet_name, tasks in grouped.items():
        print(f"\n  🐶  {pet_name}")
        print(f"  {THIN_DIVIDER}")
        for t in tasks:
            icon      = STATUS_ICON.get(t.status.value, "?")
            time_str  = t.time_label.ljust(7)
            pri_bar   = "▮" * t.priority + "▯" * (5 - t.priority)
            print(
                f"  {icon}  {time_str}  [{pri_bar}]  "
                f"{t.name:<22}  {t.duration:>3} min  |  {t.frequency.value}"
            )

    summary   = scheduler.completion_summary()
    remaining = scheduler.total_duration(status=Status.PENDING)
    print(f"\n  {THIN_DIVIDER}")
    print(
        f"  Tasks  —  "
        f"Pending: {summary['pending']}  "
        f"In-progress: {summary['in_progress']}  "
        f"Done: {summary['done']}  "
        f"Skipped: {summary['skipped']}"
    )
    print(f"  Time remaining today: {remaining} min")
    print(f"  {DIVIDER}\n")


def print_task_list(tasks: list[Task], label: str) -> None:
    """Generic helper used by the sort/filter demos below."""
    print(f"\n  {label}")
    print(f"  {THIN_DIVIDER}")
    if not tasks:
        print("  (no tasks)")
        return
    for t in tasks:
        icon     = STATUS_ICON.get(t.status.value, "?")
        pri_bar  = "▮" * t.priority + "▯" * (5 - t.priority)
        time_str = t.time_label.ljust(7)
        print(
            f"  {icon}  {time_str}  [{pri_bar}]  "
            f"{t.name:<22}  {t.duration:>3} min  |  {t.status.value}"
        )


# ---------------------------------------------------------------------------
# Setup: owner, pets, and tasks  (added out-of-order on purpose)
# ---------------------------------------------------------------------------

def build_demo() -> tuple[Owner, Scheduler]:
    owner = Owner("Jordan", email="jordan@pawpal.app")

    bella = Pet("Bella", species="dog",    breed="Golden Retriever", age=4.0,
                notes="Allergic to chicken-based treats.")
    mochi = Pet("Mochi", species="cat",    breed="Ragdoll",          age=2.5,
                notes="Shy around strangers; prefers quiet feeding spot.")
    finn  = Pet("Finn",  species="rabbit", breed="Holland Lop",      age=1.0,
                notes="Free-roams in the living room after 18:00.")

    owner.add_pet(bella)
    owner.add_pet(mochi)
    owner.add_pet(finn)

    # --- Bella — tasks added deliberately out of chronological order --------
    bella.add_task(Task(
        name="Feed dinner",
        description="1 cup grain-free kibble.",
        duration=10, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(18, 0),
    ))
    bella.add_task(Task(
        name="Teeth brushing",
        description="Enzymatic toothpaste, 2 min per side.",
        duration=5, priority=2, frequency=Frequency.WEEKLY,
        scheduled_time=time(20, 0),
    ))
    bella.add_task(Task(
        name="Morning walk",
        description="30-min neighbourhood loop; pick up after her.",
        duration=30, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(7, 0),
    ))
    bella.add_task(Task(
        name="Training session",
        description="15-min recall and sit-stay drills.",
        duration=15, priority=3, frequency=Frequency.DAILY,
        scheduled_time=time(9, 0),
    ))
    bella.add_task(Task(
        name="Evening walk",
        description="45-min park walk; allow off-lead in the fenced area.",
        duration=45, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(17, 30),
    ))
    bella.add_task(Task(
        name="Feed breakfast",
        description="1 cup grain-free kibble + joint supplement.",
        duration=10, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(7, 30),
    ))

    # --- Mochi — tasks added out of order -----------------------------------
    mochi.add_task(Task(
        name="Brush coat",
        description="Gentle slicker brush to prevent matting.",
        duration=10, priority=2, frequency=Frequency.WEEKLY,
        scheduled_time=time(19, 0),
    ))
    mochi.add_task(Task(
        name="Feed dinner",
        description="Half pouch of salmon pâté.",
        duration=5, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(18, 30),
    ))
    mochi.add_task(Task(
        name="Litter scoop",
        description="Scoop clumps; top up litter if below 3 cm.",
        duration=5, priority=4, frequency=Frequency.DAILY,
        scheduled_time=time(8, 0),
    ))
    mochi.add_task(Task(
        name="Feed breakfast",
        description="Half pouch of tuna pâté + fresh water.",
        duration=5, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(7, 15),
    ))
    mochi.add_task(Task(
        name="Wand play",
        description="10-min interactive session to prevent boredom.",
        duration=10, priority=3, frequency=Frequency.DAILY,
        scheduled_time=time(11, 0),
    ))

    # --- Finn — tasks added out of order ------------------------------------
    finn.add_task(Task(
        name="Nail trim",
        description="Front and rear claws; use small animal clippers.",
        duration=15, priority=2, frequency=Frequency.ONCE,
        scheduled_time=time(10, 0),
    ))
    finn.add_task(Task(
        name="Free-roam time",
        description="Open pen gate; rabbit-proof area checked beforehand.",
        duration=60, priority=3, frequency=Frequency.DAILY,
        scheduled_time=time(18, 0),
    ))
    finn.add_task(Task(
        name="Fresh hay & water",
        description="Refill timothy hay rack; rinse and refill water bottle.",
        duration=5, priority=5, frequency=Frequency.DAILY,
        scheduled_time=time(8, 30),
    ))
    finn.add_task(Task(
        name="Veggie portion",
        description="Small handful of romaine, parsley, and carrot tops.",
        duration=5, priority=4, frequency=Frequency.DAILY,
        scheduled_time=time(12, 0),
    ))

    # --- Deliberate conflicts for warn_conflicts() demo --------------------
    # Clash 1 — same pet: two Bella tasks at 07:00 (Morning walk already exists)
    bella.add_task(Task(
        name="Flea treatment",
        description="Apply spot-on treatment between shoulder blades.",
        duration=5, priority=3, frequency=Frequency.MONTHLY,
        scheduled_time=time(7, 0),
    ))

    # Clash 2 — cross-pet: Mochi's Feed breakfast (07:15) vs a new Finn task
    finn.add_task(Task(
        name="Morning weight check",
        description="Weigh on digital scale; log in health notebook.",
        duration=5, priority=2, frequency=Frequency.WEEKLY,
        scheduled_time=time(7, 15),
    ))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    return owner, scheduler


# ---------------------------------------------------------------------------
# Sort & filter demo
# ---------------------------------------------------------------------------

def run_sort_filter_demo(scheduler: Scheduler) -> None:
    """
    Exercise sort_by_time(), by_priority(), by_status(), by_frequency(),
    overdue(), and filter_tasks() against the schedule built from
    out-of-order task input.
    """

    # 1. sort_by_time — should reorder regardless of insertion order
    section("🕐  sort_by_time()  —  all tasks in HH:MM order")
    print_task_list(scheduler.sort_by_time(), "Chronological (untimed tasks appear last)")

    # 2. by_priority — high-stakes tasks only (P5 and P4)
    section("⚡  by_priority()  —  priority 5 tasks")
    print_task_list(scheduler.by_priority(5), "Priority 5 tasks")

    section("⚡  by_priority()  —  priority 4 tasks")
    print_task_list(scheduler.by_priority(4), "Priority 4 tasks")

    # 3. by_status — advance a few tasks first so there's mixed state to filter
    section("🔄  by_status()  —  advancing tasks to create mixed statuses")
    pending = scheduler.by_status(Status.PENDING)

    # Mark the first two pending tasks IN_PROGRESS then DONE
    done_tasks   = pending[:2]
    skip_task    = pending[2]
    active_tasks = pending[3:5]

    for t in done_tasks:
        scheduler.advance(t.task_id)   # PENDING -> IN_PROGRESS
        scheduler.advance(t.task_id)   # IN_PROGRESS -> DONE

    scheduler.skip(skip_task.task_id)  # PENDING -> SKIPPED

    for t in active_tasks:
        scheduler.advance(t.task_id)   # PENDING -> IN_PROGRESS

    print_task_list(scheduler.by_status(Status.PENDING),     "Pending tasks")
    print_task_list(scheduler.by_status(Status.IN_PROGRESS), "In-progress tasks")
    print_task_list(scheduler.by_status(Status.DONE),        "Done tasks")
    print_task_list(scheduler.by_status(Status.SKIPPED),     "Skipped tasks")

    # 4. by_frequency
    section("🔁  by_frequency()  —  daily vs weekly vs once")
    print_task_list(scheduler.by_frequency(Frequency.DAILY),  "Daily tasks")
    print_task_list(scheduler.by_frequency(Frequency.WEEKLY), "Weekly tasks")
    print_task_list(scheduler.by_frequency(Frequency.ONCE),   "One-off tasks")

    # 7. warn_conflicts() — lightweight overlap detection
    section("⚠️   warn_conflicts()  —  lightweight scheduling overlap check")
    warnings = scheduler.warn_conflicts()
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  ✓  No scheduling conflicts detected.")

    # Full structured report for comparison
    section("📋  print_conflicts()  —  full structured conflict report")
    scheduler.print_conflicts()
    #    result is deterministic regardless of when the test is run
    from datetime import date, datetime
    ref = datetime.combine(date.today(), time(13, 0))
    section(f"⏰  overdue()  —  pending tasks scheduled before {ref.strftime('%H:%M')}")
    print_task_list(scheduler.overdue(reference=ref), f"Overdue before {ref.strftime('%H:%M')}")

    # ------------------------------------------------------------------
    # 6. filter_tasks() — multi-axis filter: status and/or pet name
    # ------------------------------------------------------------------

    section("🔍  filter_tasks()  —  multi-axis status + pet name filtering")

    # 6a. All tasks belonging to Bella (any status)
    print_task_list(
        scheduler.filter_tasks(pet_name="Bella"),
        "Bella — all tasks (any status)",
    )

    # 6b. Only Bella's pending tasks — both axes active
    print_task_list(
        scheduler.filter_tasks(status=Status.PENDING, pet_name="Bella"),
        "Bella — pending tasks only",
    )

    # 6c. All done tasks across every pet — status axis only
    print_task_list(
        scheduler.filter_tasks(status=Status.DONE),
        "All pets — done tasks only",
    )

    # 6d. All of Finn's tasks regardless of status
    print_task_list(
        scheduler.filter_tasks(pet_name="Finn"),
        "Finn — all tasks (any status)",
    )

    # 6e. Mochi's in-progress tasks — should be empty or populated
    #     depending on which tasks were advanced above
    print_task_list(
        scheduler.filter_tasks(status=Status.IN_PROGRESS, pet_name="Mochi"),
        "Mochi — in-progress tasks only",
    )

    # 6f. No filters supplied — should mirror the full schedule
    print_task_list(
        scheduler.filter_tasks(),
        "No filters — full schedule (identity case)",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import sys
    if "--smoke" in sys.argv:
        run_smoke_test()
        return

    owner, scheduler = build_demo()

    # Full schedule view (priority-sorted, as generated)
    print_schedule(scheduler)

    # Sort & filter demos
    run_sort_filter_demo(scheduler)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> None:
    """Quick end-to-end sanity check for core system behaviour."""
    owner = Owner("Alex", email="alex@pawpal.app")
    bella = Pet("Bella", species="dog", breed="Labrador", age=3.0)
    mochi = Pet("Mochi", species="cat", breed="Ragdoll",  age=1.5)
    owner.add_pet(bella)
    owner.add_pet(mochi)

    bella.add_task(Task("Morning walk",   "30 min neighbourhood walk", 30, 5, Frequency.DAILY, scheduled_time=time(7, 0)))
    bella.add_task(Task("Feed breakfast", "1 cup dry kibble",          10, 5, Frequency.DAILY, scheduled_time=time(7, 30)))
    bella.add_task(Task("Grooming",       "Full brush + ear check",    45, 3, Frequency.WEEKLY))
    bella.add_task(Task("Vet check-up",   "Annual booster shots",      60, 4, Frequency.ONCE,  scheduled_time=time(10, 0)))

    mochi.add_task(Task("Feed breakfast", "Half pouch wet food",       10, 5, Frequency.DAILY, scheduled_time=time(7, 15)))
    mochi.add_task(Task("Litter clean",   "Scoop and top up litter",   10, 4, Frequency.DAILY, scheduled_time=time(8, 0)))
    mochi.add_task(Task("Playtime",       "Wand toy session",          15, 2, Frequency.DAILY))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    scheduler.display()

    walk = bella.all_tasks()[0]
    scheduler.advance(walk.task_id)
    scheduler.advance(walk.task_id)

    feed = bella.all_tasks()[1]
    scheduler.skip(feed.task_id)

    scheduler.display(show_done=True)
    print(owner.dashboard())