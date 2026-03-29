"""
test_pawpal.py
Unit tests for PawPal core classes.
Run with: python -m pytest test_pawpal.py -v
"""

import pytest

from pawpal_system import Frequency, Pet, Status, Task


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