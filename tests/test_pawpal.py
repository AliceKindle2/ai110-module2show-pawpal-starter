"""
test_pawpal.py
Unit tests for PawPal core classes.
Run with: python -m pytest test_pawpal.py -v
"""

import pytest
from datetime import date, time, timedelta

from pawpal_system import Frequency, Owner, Pet, Scheduler, Status, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_task() -> Task:
    """A minimal valid PENDING task."""
    return Task(
        name="Morning walk",
        description="30-min neighbourhood loop.",
        duration=30,
        priority=4,
        frequency=Frequency.DAILY,
    )


@pytest.fixture
def basic_pet() -> Pet:
    """A pet with no tasks attached."""
    return Pet("Bella", species="dog", breed="Golden Retriever", age=3.0)


@pytest.fixture
def owner_with_pet() -> tuple[Owner, Pet]:
    """An Owner with one Pet already registered."""
    owner = Owner("Alice")
    pet = Pet("Rex", "dog", age=3)
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# Task completion tests
# ---------------------------------------------------------------------------

class TestTaskCompletion:

    def test_initial_status_is_pending(self, basic_task: Task) -> None:
        """A freshly created task must start as PENDING."""
        assert basic_task.status == Status.PENDING

    def test_mark_in_progress_changes_status(self, basic_task: Task) -> None:
        """mark_in_progress() should transition PENDING → IN_PROGRESS."""
        basic_task.mark_in_progress()
        assert basic_task.status == Status.IN_PROGRESS

    def test_mark_done_from_in_progress(self, basic_task: Task) -> None:
        """mark_done() should transition IN_PROGRESS → DONE."""
        basic_task.mark_in_progress()
        basic_task.mark_done()
        assert basic_task.status == Status.DONE

    def test_mark_done_directly_from_pending(self, basic_task: Task) -> None:
        """mark_done() is also valid directly from PENDING."""
        basic_task.mark_done()
        assert basic_task.status == Status.DONE

    def test_completed_at_is_set_on_done(self, basic_task: Task) -> None:
        """completed_at timestamp must be populated when a task is marked done."""
        assert basic_task.completed_at is None
        basic_task.mark_done()
        assert basic_task.completed_at is not None

    def test_is_complete_property(self, basic_task: Task) -> None:
        """is_complete should return True only after mark_done()."""
        assert not basic_task.is_complete
        basic_task.mark_done()
        assert basic_task.is_complete

    def test_cannot_complete_a_skipped_task(self, basic_task: Task) -> None:
        """mark_done() on a SKIPPED task must raise RuntimeError."""
        basic_task.mark_skipped()
        with pytest.raises(RuntimeError):
            basic_task.mark_done()

    def test_cannot_start_a_done_task(self, basic_task: Task) -> None:
        """mark_in_progress() on a DONE task must raise RuntimeError."""
        basic_task.mark_done()
        with pytest.raises(RuntimeError):
            basic_task.mark_in_progress()


# ---------------------------------------------------------------------------
# Task addition tests
# ---------------------------------------------------------------------------

class TestTaskAddition:

    def test_new_pet_has_no_tasks(self, basic_pet: Pet) -> None:
        """A newly created pet must have an empty task list."""
        assert len(basic_pet.all_tasks()) == 0

    def test_adding_one_task_increases_count(self, basic_pet: Pet, basic_task: Task) -> None:
        """Adding a single task should bring the count from 0 to 1."""
        basic_pet.add_task(basic_task)
        assert len(basic_pet.all_tasks()) == 1

    def test_adding_multiple_tasks_increments_correctly(self, basic_pet: Pet) -> None:
        """Each added task should increase the count by exactly one."""
        for i in range(1, 4):
            basic_pet.add_task(Task(f"Task {i}", "desc", duration=10, priority=i))
            assert len(basic_pet.all_tasks()) == i

    def test_added_task_is_retrievable(self, basic_pet: Pet, basic_task: Task) -> None:
        """The task returned by get_task() must be the exact object that was added."""
        basic_pet.add_task(basic_task)
        retrieved = basic_pet.get_task(basic_task.task_id)
        assert retrieved is basic_task

    def test_duplicate_task_raises_error(self, basic_pet: Pet, basic_task: Task) -> None:
        """Adding the same Task object twice must raise ValueError."""
        basic_pet.add_task(basic_task)
        with pytest.raises(ValueError):
            basic_pet.add_task(basic_task)

    def test_task_count_unchanged_after_duplicate_attempt(
        self, basic_pet: Pet, basic_task: Task
    ) -> None:
        """A failed duplicate add must not silently mutate the task list."""
        basic_pet.add_task(basic_task)
        with pytest.raises(ValueError):
            basic_pet.add_task(basic_task)
        assert len(basic_pet.all_tasks()) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

class TestSortingCorrectness:

    def test_tasks_returned_in_chronological_order(self, owner_with_pet: tuple[Owner, Pet]) -> None:
        """Tasks added out of order should be sorted ascending by scheduled_time."""
        owner, pet = owner_with_pet
        today = date.today()

        # scheduled_time hours 1, 2, 3 give a clear chronological order to assert against
        for days, name in [(3, "Feed Rex"), (1, "Vet checkup"), (2, "Bath time")]:
            pet.add_task(Task(
                name, "", 10, 1,
                scheduled_time=time(days, 0),
                due_date=today + timedelta(days=days),
            ))

        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.generate_schedule()
        times = [t.scheduled_time for t in sorted_tasks]

        assert times == sorted(times), (
            f"Expected chronological order, got: {times}"
        )


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

class TestRecurrenceLogic:

    def test_completing_daily_task_creates_next_day_task(
        self, owner_with_pet: tuple[Owner, Pet]
    ) -> None:
        """Advancing a daily task to DONE should spawn a new PENDING task for due_date + 1."""
        owner, pet = owner_with_pet
        today = date.today()

        task = Task(
            "Morning walk", "", 30, 3,
            frequency=Frequency.DAILY,
            due_date=today,
        )
        pet.add_task(task)

        scheduler = Scheduler(owner)
        scheduler.generate_schedule()

        scheduler.advance(task.task_id)  # PENDING → IN_PROGRESS
        scheduler.advance(task.task_id)  # IN_PROGRESS → DONE, spawns successor

        pending = pet.pending_tasks()
        assert any(t.name == "Morning walk" for t in pending), (
            "Recurring task title should reappear after completion."
        )
        assert any(t.due_date == today + timedelta(days=1) for t in pending), (
            f"Expected successor on {today + timedelta(days=1)}, "
            f"got: {[t.due_date for t in pending]}"
        )


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection:

    def test_duplicate_time_flags_conflict(
        self, owner_with_pet: tuple[Owner, Pet]
    ) -> None:
        """Two tasks for the same pet at the same scheduled_time should be flagged as a conflict."""
        owner, pet = owner_with_pet
        feed_time = time(8, 0)
        today = date.today()

        pet.add_task(Task("Feed Bella", "", 10, 2, scheduled_time=feed_time, due_date=today))
        pet.add_task(Task("Give meds",  "",  5, 2, scheduled_time=feed_time, due_date=today))

        scheduler = Scheduler(owner)
        scheduler.generate_schedule()

        conflicts = scheduler.detect_conflicts()

        assert len(conflicts) == 1, (
            f"Expected 1 conflict, got {len(conflicts)}"
        )
        assert conflicts[0].time_str == "08:00", (
            f"Expected conflict at 08:00, got: {conflicts[0].time_str}"
        )