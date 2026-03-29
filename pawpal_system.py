"""
pawpal_system.py
Core implementation of the PawPal pet care system.
"""

from __future__ import annotations

import heapq
from collections import deque
from itertools import combinations
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Callable, Generator, Iterator, Optional
from uuid import uuid4


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Frequency(Enum):
    ONCE       = "once"
    DAILY      = "daily"
    WEEKLY     = "weekly"
    AS_NEEDED  = "as_needed"


class Status(Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    SKIPPED     = "skipped"


# ---------------------------------------------------------------------------
# State-transition table (used by Task)
# ---------------------------------------------------------------------------

_ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.PENDING:     {Status.IN_PROGRESS, Status.SKIPPED},
    Status.IN_PROGRESS: {Status.DONE, Status.SKIPPED},
    Status.DONE:        set(),
    Status.SKIPPED:     set(),
}

# Maps recurring frequencies to their forward timedelta.
# ONCE and AS_NEEDED have no entry — get() returns None for them.
_RECURRENCE_DELTA: dict[Frequency, timedelta] = {
    Frequency.DAILY:  timedelta(days=1),
    Frequency.WEEKLY: timedelta(weeks=1),
}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """
    A single care activity assigned to a pet.

    Attributes:
        name           : Short label, e.g. "Morning walk".
        description    : Detailed instructions for the caregiver.
        duration       : Estimated time in minutes (must be > 0).
        priority       : 1 (low) – 5 (high).
        frequency      : How often the task recurs.
        scheduled_time : Wall-clock time the task should start (optional).
        due_date       : Calendar date the task is due (optional).
        status         : Current lifecycle state of the task.
        task_id        : Immutable unique identifier (auto-generated).
        created_at     : Timestamp of creation (auto-generated).
        completed_at   : Timestamp set when status transitions to DONE.
    """

    name: str
    description: str
    duration: int
    priority: int
    frequency: Frequency = Frequency.DAILY
    scheduled_time: Optional[time] = None
    due_date: Optional[date] = None
    status: Status = field(default=Status.PENDING, init=True)
    task_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    created_at: datetime = field(default_factory=datetime.now, init=False)
    completed_at: Optional[datetime] = field(default=None, init=False)
    _sort_key: tuple = field(init=False, repr=False, compare=False)

    # ---- validation --------------------------------------------------------

    def __post_init__(self) -> None:
        self._validate_duration(self.duration)
        self._validate_priority(self.priority)
        self._rebuild_sort_key()

    @staticmethod
    def _validate_duration(v: int) -> None:
        if v <= 0:
            raise ValueError(f"Duration must be > 0 minutes, got {v}")

    @staticmethod
    def _validate_priority(v: int) -> None:
        if not (1 <= v <= 5):
            raise ValueError(f"Priority must be 1–5, got {v}")

    def _rebuild_sort_key(self) -> None:
        if self.scheduled_time is not None:
            ref_date = self.due_date or date.today()
            dt = datetime.combine(ref_date, self.scheduled_time)
        else:
            dt = datetime.max
        self._sort_key = (-self.priority, dt, self.duration)

    # ---- mutation ----------------------------------------------------------

    def edit(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        duration: Optional[int] = None,
        priority: Optional[int] = None,
        frequency: Optional[Frequency] = None,
        scheduled_time: Optional[time] = None,
        due_date: Optional[date] = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if duration is not None:
            self._validate_duration(duration)
            self.duration = duration
        if priority is not None:
            self._validate_priority(priority)
            self.priority = priority
        if frequency is not None:
            self.frequency = frequency
        if scheduled_time is not None:
            self.scheduled_time = scheduled_time
        if due_date is not None:
            self.due_date = due_date
        self._rebuild_sort_key()

    def _transition(self, target: Status) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            allowed = {s.value for s in _ALLOWED_TRANSITIONS[self.status]}
            raise RuntimeError(
                f"Cannot move task {self.name!r} from "
                f"{self.status.value!r} to {target.value!r}. "
                f"Allowed next states: {allowed or {'none'}}"
            )
        self.status = target

    def mark_in_progress(self) -> None:
        """Transition the task from PENDING to IN_PROGRESS."""
        self._transition(Status.IN_PROGRESS)

    def mark_done(self) -> Optional["Task"]:
        """
        Transition the task to DONE and record the completion timestamp.

        For DAILY and WEEKLY tasks, spawns and returns a fresh Task for the
        next occurrence. The new due_date is anchored to self.due_date (or
        today as a fallback) plus the recurrence delta, so completing a task
        late does not silently drift the entire schedule forward.

        Returns:
            A new PENDING Task for the next cycle (DAILY/WEEKLY), or None
            for ONCE and AS_NEEDED tasks.
        """
        self._transition(Status.DONE)
        self.completed_at = datetime.now()
        return self._spawn_next_occurrence()

    def _spawn_next_occurrence(self) -> Optional["Task"]:
        """
        Return a successor Task for the next cycle if this task recurs.

        Anchors the new due_date to self.due_date (falling back to today) so
        completing a task late does not permanently shift the schedule.
        The successor inherits all authoring fields but gets a fresh task_id,
        created_at, and starts in PENDING with no completed_at.
        """
        delta = _RECURRENCE_DELTA.get(self.frequency)
        if delta is None:
            return None

        base_date = self.due_date or date.today()
        next_task = Task(
            name           = self.name,
            description    = self.description,
            duration       = self.duration,
            priority       = self.priority,
            frequency      = self.frequency,
            scheduled_time = self.scheduled_time,
            due_date       = base_date + delta,
        )
        return next_task

    def mark_skipped(self) -> None:
        """Mark the task as SKIPPED."""
        self._transition(Status.SKIPPED)

    def reset(self) -> None:
        """Return a recurring task to PENDING for the next cycle."""
        if self.frequency == Frequency.ONCE:
            raise RuntimeError("One-off tasks cannot be reset")
        self.status = Status.PENDING
        self.completed_at = None

    # ---- display -----------------------------------------------------------

    @property
    def is_complete(self) -> bool:
        return self.status == Status.DONE

    @property
    def time_label(self) -> str:
        parts = []
        if self.due_date:
            parts.append(self.due_date.strftime("%Y-%m-%d"))
        if self.scheduled_time:
            parts.append(self.scheduled_time.strftime("%H:%M"))
        return " ".join(parts) if parts else "anytime"

    def summary(self) -> str:
        return (
            f"[P{self.priority}] {self.name} | {self.duration} min | "
            f"{self.time_label} | {self.frequency.value} | {self.status.value}"
        )

    def __repr__(self) -> str:
        return f"Task(name={self.name!r}, priority={self.priority}, status={self.status.value!r})"

    def __lt__(self, other: Task) -> bool:
        return self._sort_key < other._sort_key


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """Stores pet profile information and owns a dict of Tasks keyed by task_id."""

    def __init__(
        self,
        name: str,
        species: str,
        breed: str = "",
        age: float = 0.0,
        notes: str = "",
    ) -> None:
        if age < 0:
            raise ValueError("Age cannot be negative")
        self.name = name
        self.species = species.lower()
        self.breed = breed
        self.age = age
        self.notes = notes
        self.pet_id: str = str(uuid4())
        self._tasks: dict[str, Task] = {}
        self._done_count: int = 0

    def edit_info(
        self,
        *,
        name: Optional[str] = None,
        species: Optional[str] = None,
        breed: Optional[str] = None,
        age: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        if name is not None:
            self.name = name
        if species is not None:
            self.species = species.lower()
        if breed is not None:
            self.breed = breed
        if age is not None:
            if age < 0:
                raise ValueError("Age cannot be negative")
            self.age = age
        if notes is not None:
            self.notes = notes

    def add_task(self, task: Task) -> None:
        if task.task_id in self._tasks:
            raise ValueError(f"Task {task.task_id!r} is already assigned to {self.name}")
        self._tasks[task.task_id] = task
        if task.is_complete:
            self._done_count += 1

    def remove_task(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"No task with id {task_id!r} on pet {self.name!r}")
        task = self._tasks.pop(task_id)
        if task.is_complete:
            self._done_count -= 1
        return task

    def get_task(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"No task with id {task_id!r} on pet {self.name!r}")
        return self._tasks[task_id]

    def all_tasks(self, *, status: Optional[Status] = None) -> list[Task]:
        if status is not None:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())

    def pending_tasks(self) -> list[Task]:
        return self.all_tasks(status=Status.PENDING)

    def completed_tasks(self) -> list[Task]:
        return self.all_tasks(status=Status.DONE)

    def notify_status_change(self, task: Task, old_status: Status) -> None:
        was_done = old_status == Status.DONE
        is_done  = task.is_complete
        if is_done and not was_done:
            self._done_count += 1
        elif was_done and not is_done:
            self._done_count -= 1

    def reset_recurring_tasks(self, *, frequency: Optional[Frequency] = None) -> int:
        count = 0
        for t in self._tasks.values():
            if t.frequency == Frequency.ONCE:
                continue
            if frequency is not None and t.frequency != frequency:
                continue
            if t.status in (Status.DONE, Status.SKIPPED):
                t.reset()
                count += 1
        self._done_count = sum(1 for t in self._tasks.values() if t.is_complete)
        return count

    @property
    def completion_rate(self) -> float:
        if not self._tasks:
            return 0.0
        return self._done_count / len(self._tasks)

    def profile(self) -> str:
        breed_str = f" ({self.breed})" if self.breed else ""
        return (
            f"{self.name} — {self.species}{breed_str}, "
            f"{self.age}y | {len(self._tasks)} tasks | "
            f"{self.completion_rate:.0%} complete"
        )

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self._tasks)})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages a roster of Pets and provides aggregate access to their Tasks."""

    def __init__(self, name: str, email: str = "") -> None:
        self.name = name
        self.email = email
        self.owner_id: str = str(uuid4())
        self._pets: dict[str, Pet] = {}
        self._pets_by_name: dict[str, list[Pet]] = {}

    def edit_info(self, *, name: Optional[str] = None, email: Optional[str] = None) -> None:
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email

    def add_pet(self, pet: Pet) -> None:
        if pet.pet_id in self._pets:
            raise ValueError(f"{pet.name} is already registered to {self.name}")
        self._pets[pet.pet_id] = pet
        self._pets_by_name.setdefault(pet.name.lower(), []).append(pet)

    def remove_pet(self, pet_id: str) -> Pet:
        if pet_id not in self._pets:
            raise KeyError(f"No pet with id {pet_id!r} registered to {self.name}")
        pet = self._pets.pop(pet_id)
        name_key = pet.name.lower()
        self._pets_by_name[name_key].remove(pet)
        if not self._pets_by_name[name_key]:
            del self._pets_by_name[name_key]
        return pet

    def get_pet(self, pet_id: str) -> Pet:
        if pet_id not in self._pets:
            raise KeyError(f"No pet with id {pet_id!r}")
        return self._pets[pet_id]

    def all_pets(self) -> list[Pet]:
        return list(self._pets.values())

    def find_pets(self, *, species: Optional[str] = None, name: Optional[str] = None) -> list[Pet]:
        if name is not None:
            results = list(self._pets_by_name.get(name.lower(), []))
        else:
            results = self.all_pets()
        if species:
            results = [p for p in results if p.species == species.lower()]
        return results

    def iter_tasks(
        self, *, status: Optional[Status] = None
    ) -> Generator[tuple[Pet, Task], None, None]:
        for pet in self._pets.values():
            for task in pet.all_tasks(status=status):
                yield pet, task

    def all_tasks(self, *, status: Optional[Status] = None) -> list[tuple[Pet, Task]]:
        return list(self.iter_tasks(status=status))

    def pending_tasks(self) -> list[tuple[Pet, Task]]:
        return self.all_tasks(status=Status.PENDING)

    def add_task_to_pet(self, pet_id: str, task: Task) -> None:
        self.get_pet(pet_id).add_task(task)

    def remove_task_from_pet(self, pet_id: str, task_id: str) -> Task:
        return self.get_pet(pet_id).remove_task(task_id)

    def reset_all_recurring(
        self, *, frequency: Optional[Frequency] = None
    ) -> dict[str, int]:
        return {
            p.name: p.reset_recurring_tasks(frequency=frequency)
            for p in self._pets.values()
        }

    @property
    def overall_completion_rate(self) -> float:
        total = done = 0
        for _, t in self.iter_tasks():
            total += 1
            if t.is_complete:
                done += 1
        return done / total if total else 0.0

    def dashboard(self) -> str:
        lines = [f"=== {self.name}'s PawPal Dashboard ==="]
        for pet in self._pets.values():
            lines.append(f"  {pet.profile()}")
            for task in pet.all_tasks():
                lines.append(f"      • {task.summary()}")
        lines.append(f"  Overall completion: {self.overall_completion_rate:.0%}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, pets={len(self._pets)})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    The 'Brain' of PawPal.

    Retrieves tasks across all of an owner's pets, organises them into a
    priority-sorted schedule, and provides tools to filter, iterate, and
    advance task states.
    """

    HISTORY_MAXLEN = 20

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.schedule: list[Task] = []
        self._schedule_index: dict[str, Task] = {}
        self._history: deque[dict] = deque(maxlen=self.HISTORY_MAXLEN)

    # ---- schedule generation -----------------------------------------------

    def generate_schedule(
        self,
        *,
        status_filter: Optional[Status] = Status.PENDING,
        pet_ids: Optional[list[str]] = None,
        custom_tasks: Optional[list[Task]] = None,
    ) -> list[Task]:
        if self.schedule:
            self._snapshot()
        if custom_tasks is not None:
            self._validate_tasks_belong_to_owner(custom_tasks)
            source = custom_tasks
        else:
            pets = (
                [self.owner.get_pet(pid) for pid in pet_ids]
                if pet_ids else self.owner.all_pets()
            )
            source = [
                task for pet in pets
                for task in (pet.all_tasks(status=status_filter) if status_filter else pet.all_tasks())
            ]
        self.schedule = self._priority_sort(source)
        self._schedule_index = {t.task_id: t for t in self.schedule}
        return self.schedule

    @staticmethod
    def _priority_sort(tasks: list[Task]) -> list[Task]:
        heap: list[tuple] = []
        for t in tasks:
            heapq.heappush(heap, (t._sort_key, t))
        return [heapq.heappop(heap)[1] for _ in range(len(heap))]

    def _validate_tasks_belong_to_owner(self, tasks: list[Task]) -> None:
        owner_task_ids = {t.task_id for pet in self.owner.all_pets() for t in pet.all_tasks()}
        for t in tasks:
            if t.task_id not in owner_task_ids:
                raise ValueError(f"Task {t.name!r} does not belong to owner {self.owner.name!r}")

    # ---- task iteration & state advancement --------------------------------

    def __iter__(self) -> Iterator[Task]:
        return iter(self.schedule)

    def next_task(self) -> Optional[Task]:
        for t in self.schedule:
            if t.status == Status.PENDING:
                return t
        return None

    def advance(self, task_id: str) -> Status:
        """
        Step a task through PENDING → IN_PROGRESS → DONE.

        When a DAILY or WEEKLY task reaches DONE, the successor returned by
        mark_done() is automatically registered on the owning Pet and
        appended to the live schedule so it appears in the next filter or
        sort call without requiring a full regenerate_schedule().
        """
        task = self._find_in_schedule(task_id)

        if task.status == Status.PENDING:
            task.mark_in_progress()

        elif task.status == Status.IN_PROGRESS:
            next_task = task.mark_done()
            if next_task is not None:
                # Find the pet that owns this task and attach the successor.
                for pet in self.owner.all_pets():
                    if task.task_id in {t.task_id for t in pet.all_tasks()}:
                        pet.add_task(next_task)
                        self.schedule.append(next_task)
                        self._schedule_index[next_task.task_id] = next_task
                        break

        else:
            raise RuntimeError(f"Task {task.name!r} is already {task.status.value!r}")

        return task.status

    def skip(self, task_id: str) -> None:
        self._find_in_schedule(task_id).mark_skipped()

    def _find_in_schedule(self, task_id: str) -> Task:
        try:
            return self._schedule_index[task_id]
        except KeyError:
            raise KeyError(f"Task {task_id!r} not found in current schedule")

    # ---- filtering helpers -------------------------------------------------

    def filter(self, predicate: Callable[[Task], bool]) -> list[Task]:
        return [t for t in self.schedule if predicate(t)]

    def by_status(self, status: Status) -> list[Task]:
        return self.filter(lambda t: t.status == status)

    def by_priority(self, priority: int) -> list[Task]:
        return self.filter(lambda t: t.priority == priority)

    def by_frequency(self, frequency: Frequency) -> list[Task]:
        return self.filter(lambda t: t.frequency == frequency)

    def filter_tasks(
        self,
        *,
        status: Optional[Status] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """
        Return scheduled tasks filtered by completion status and/or pet name.

        Both parameters are optional and additive — supplying both returns
        only tasks that satisfy both conditions simultaneously.
        """
        task_ids_for_pet: Optional[set[str]] = None
        if pet_name is not None:
            matched_pets = self.owner.find_pets(name=pet_name)
            task_ids_for_pet = {
                task.task_id
                for pet in matched_pets
                for task in pet.all_tasks()
            }

        return [
            t for t in self.schedule
            if (status is None or t.status == status)
            and (task_ids_for_pet is None or t.task_id in task_ids_for_pet)
        ]

    def sort_by_time(self) -> list[Task]:
        """
        Return scheduled tasks sorted by scheduled_time ascending (HH:MM order).
        Tasks without a scheduled_time are placed at the end.
        """
        _UNTIMED_SENTINEL = "99:99"
        return sorted(
            self.schedule,
            key=lambda t: (
                t.scheduled_time.strftime("%H:%M")
                if t.scheduled_time is not None
                else _UNTIMED_SENTINEL
            ),
        )

    def overdue(self, reference: Optional[datetime] = None) -> list[Task]:
        ref = reference or datetime.now()
        def _is_overdue(t: Task) -> bool:
            if t.status != Status.PENDING or t.scheduled_time is None:
                return False
            task_date = t.due_date or date.today()
            return datetime.combine(task_date, t.scheduled_time) < ref
        return self.filter(_is_overdue)

    # ---- conflict detection ------------------------------------------------

    @dataclass
    class ConflictResult:
        """
        Holds a pair of conflicting tasks and the pet(s) they belong to.

        Attributes:
            task_a    : First task in the conflict.
            task_b    : Second task in the conflict.
            pet_a     : Pet that owns task_a.
            pet_b     : Pet that owns task_b (may equal pet_a for same-pet conflicts).
            same_pet  : True when both tasks belong to the same pet.
            time_str  : The shared scheduled time as "HH:MM".
        """
        task_a:   "Task"
        task_b:   "Task"
        pet_a:    "Pet"
        pet_b:    "Pet"
        same_pet: bool
        time_str: str

        def __str__(self) -> str:
            scope = (
                f"{self.pet_a.name}"
                if self.same_pet
                else f"{self.pet_a.name} & {self.pet_b.name}"
            )
            return (
                f"[{self.time_str}] CONFLICT ({scope}): "
                f"{self.task_a.name!r} vs {self.task_b.name!r}"
            )

    def detect_conflicts(
        self,
        *,
        status_filter: Optional[Status] = Status.PENDING,
    ) -> list["Scheduler.ConflictResult"]:
        """
        Detect tasks whose scheduled_time values overlap exactly.

        Two tasks conflict when they share the same "HH:MM" scheduled_time
        and neither has been completed or skipped (controlled by
        status_filter). Tasks without a scheduled_time are never flagged.

        Algorithm — O(n) bucket pass, not O(n²) pairwise:
          1. Build a task-id → Pet mapping in one pass over all pets.
          2. Group scheduled tasks by their "HH:MM" string into a dict.
          3. Any bucket with 2+ tasks contains at least one conflict pair;
             emit one ConflictResult per unique pair within the bucket.

        Args:
            status_filter: Only tasks in this status are examined.
                           Pass None to check tasks of every status.

        Returns:
            A list of ConflictResult objects, one per conflicting pair,
            in ascending time order. Empty list means no conflicts.
        """
        # Step 1 — build a flat task_id → Pet lookup used in step 3.
        task_to_pet: dict[str, Pet] = {
            task.task_id: pet
            for pet in self.owner.all_pets()
            for task in pet.all_tasks()
        }

        # Step 2 — bucket timed tasks by "HH:MM".
        buckets: dict[str, list[Task]] = {}
        for task in self.schedule:
            if task.scheduled_time is None:
                continue
            if status_filter is not None and task.status != status_filter:
                continue
            key = task.scheduled_time.strftime("%H:%M")
            buckets.setdefault(key, []).append(task)

        # Step 3 — emit one ConflictResult per pair inside each bucket.
        conflicts: list[Scheduler.ConflictResult] = []
        for time_str, tasks in sorted(buckets.items()):
            if len(tasks) < 2:
                continue
            for i in range(len(tasks)):
                for j in range(i + 1, len(tasks)):
                    ta, tb = tasks[i], tasks[j]
                    pet_a  = task_to_pet[ta.task_id]
                    pet_b  = task_to_pet[tb.task_id]
                    conflicts.append(
                        Scheduler.ConflictResult(
                            task_a   = ta,
                            task_b   = tb,
                            pet_a    = pet_a,
                            pet_b    = pet_b,
                            same_pet = pet_a.pet_id == pet_b.pet_id,
                            time_str = time_str,
                        )
                    )
        return conflicts

    def print_conflicts(
        self,
        *,
        status_filter: Optional[Status] = Status.PENDING,
    ) -> None:
        """Print a human-readable conflict report to stdout."""
        conflicts = self.detect_conflicts(status_filter=status_filter)
        print(f"\n  {'─' * 54}")
        print(f"  ⚠️   Conflict Report")
        print(f"  {'─' * 54}")
        if not conflicts:
            print("  ✓  No scheduling conflicts detected.")
        else:
            same   = [c for c in conflicts if c.same_pet]
            cross  = [c for c in conflicts if not c.same_pet]
            if same:
                print(f"\n  Same-pet conflicts ({len(same)})")
                for c in same:
                    print(f"    {c}")
            if cross:
                print(f"\n  Cross-pet conflicts ({len(cross)})")
                for c in cross:
                    print(f"    {c}")
        print(f"  {'─' * 54}\n")

    def warn_conflicts(
        self,
        *,
        status_filter: Optional[Status] = Status.PENDING,
    ) -> list[str]:
        """
        Lightweight conflict check that returns plain warning strings instead
        of ConflictResult objects — safe to call at any point without risk of
        an unhandled exception propagating to the caller.

        Strategy:
          - Delegates to detect_conflicts() inside a try/except so that any
            unexpected internal error is caught and surfaced as a warning
            string rather than a crash.
          - Each conflict is condensed to a single human-readable line.
          - Returns an empty list when the schedule is clean, so callers can
            use a simple truthiness check: `if scheduler.warn_conflicts(): ...`

        Args:
            status_filter: Passed through to detect_conflicts(). Defaults to
                           PENDING so only actionable conflicts are reported.

        Returns:
            A list of warning strings, one per conflicting pair. Empty when
            no conflicts are found. A single-element list containing an error
            message if the detection itself fails unexpectedly.
        """
        try:
            conflicts = self.detect_conflicts(status_filter=status_filter)
        except Exception as exc:                          # never crash the caller
            return [f"⚠️  Conflict detection unavailable: {exc}"]

        if not conflicts:
            return []

        warnings: list[str] = []
        for c in conflicts:
            scope = (
                f"{c.pet_a.name} (same pet)"
                if c.same_pet
                else f"{c.pet_a.name} & {c.pet_b.name}"
            )
            warnings.append(
                f"⚠️  [{c.time_str}] {scope}: "
                f"{c.task_a.name!r} and {c.task_b.name!r} overlap"
            )
        return warnings

    # ---- stats -------------------------------------------------------------

    def completion_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {s.value: 0 for s in Status}
        for t in self.schedule:
            summary[t.status.value] += 1
        return summary

    def total_duration(self, *, status: Optional[Status] = None) -> int:
        tasks = self.by_status(status) if status else self.schedule
        return sum(t.duration for t in tasks)

    # ---- history -----------------------------------------------------------

    def _snapshot(self) -> None:
        self._history.append({"timestamp": datetime.now(), "schedule": list(self.schedule)})

    def get_history(self) -> list[dict]:
        return list(self._history)

    # ---- display -----------------------------------------------------------

    def display(self, *, show_done: bool = True) -> None:
        if not self.schedule:
            print("No schedule generated yet. Call generate_schedule() first.")
            return
        tasks = self.schedule if show_done else self.by_status(Status.PENDING)
        print(f"\n{'─' * 52}")
        print(f"  Schedule for {self.owner.name}")
        print(f"{'─' * 52}")
        for i, t in enumerate(tasks, 1):
            print(f"  {i:>2}. {t.summary()}")
        summary = self.completion_summary()
        print(f"{'─' * 52}")
        print(
            f"  Pending: {summary['pending']}  "
            f"In-progress: {summary['in_progress']}  "
            f"Done: {summary['done']}  "
            f"Skipped: {summary['skipped']}"
        )
        print(f"  Total time remaining: {self.total_duration(status=Status.PENDING)} min")
        print(f"{'─' * 52}\n")

    def __repr__(self) -> str:
        return (
            f"Scheduler(owner={self.owner.name!r}, "
            f"tasks={len(self.schedule)}, "
            f"history={len(self._history)})"
        )