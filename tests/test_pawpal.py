from pawpal_system import Pet, Task


def test_task_completion_changes_status() -> None:
	"""Calling mark_completed should update task completion state."""
	task = Task(
		task_id="task-1",
		pet_id="pet-1",
		title="Evening walk",
		category="walk",
		duration_minutes=30,
		priority="high",
		preferred_window=None,
		due_by=None,
		recurrence="daily",
		requires_owner=True,
	)

	assert task.is_completed is False
	task.mark_completed()
	assert task.is_completed is True


def test_add_task_increases_pet_task_count() -> None:
	"""Adding a valid task should increase a pet's task count by one."""
	pet = Pet(
		pet_id="pet-1",
		name="Mochi",
		species="dog",
		age_years=3,
		weight_kg=12.0,
		medical_notes="",
	)
	task = Task(
		task_id="task-2",
		pet_id=pet.pet_id,
		title="Breakfast",
		category="feeding",
		duration_minutes=10,
		priority="medium",
		preferred_window=None,
		due_by=None,
		recurrence="daily",
		requires_owner=True,
	)

	initial_count = len(pet.tasks)
	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1
