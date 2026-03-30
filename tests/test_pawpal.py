from datetime import date, datetime, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task, TimeWindow


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


def test_generate_daily_plan_returns_entries_in_chronological_order() -> None:
	"""Generated schedule entries should be sorted by ascending start time."""
	owner = Owner(
		owner_id="owner-1",
		name="Jordan",
		contact_info="",
		available_minutes_per_day=120,
		preferred_walk_time="morning",
		notification_opt_in=True,
	)
	pet = Pet(
		pet_id="pet-chrono",
		name="Mochi",
		species="dog",
		age_years=3,
		weight_kg=12.0,
		medical_notes="",
	)
	owner.add_pet(pet)

	pet.add_task(
		Task(
			task_id="task-high",
			pet_id=pet.pet_id,
			title="Morning walk",
			category="walk",
			duration_minutes=30,
			priority="high",
			preferred_window=None,
			due_by=None,
			recurrence="daily",
			requires_owner=True,
		)
	)
	pet.add_task(
		Task(
			task_id="task-medium",
			pet_id=pet.pet_id,
			title="Breakfast",
			category="feeding",
			duration_minutes=15,
			priority="medium",
			preferred_window=None,
			due_by=None,
			recurrence="daily",
			requires_owner=True,
		)
	)
	pet.add_task(
		Task(
			task_id="task-low",
			pet_id=pet.pet_id,
			title="Brush coat",
			category="care",
			duration_minutes=10,
			priority="low",
			preferred_window=None,
			due_by=None,
			recurrence="weekly",
			requires_owner=False,
		)
	)

	scheduler = Scheduler(strategy="urgency-first", max_daily_minutes=180, respect_preferences=True)
	plan = scheduler.generate_daily_plan(
		owner=owner,
		pet=pet,
		tasks=[],
		plan_date=date(2026, 3, 30),
		day_window=TimeWindow(start_time=time(8, 0), end_time=time(12, 0)),
	)

	assert len(plan) == 3
	start_times = [entry.start_at for entry in plan]
	assert start_times == sorted(start_times)
	assert all(plan[index].end_at <= plan[index + 1].start_at for index in range(len(plan) - 1))


def test_marking_daily_task_complete_creates_next_day_task() -> None:
	"""Completing a daily task should create a new task instance for the next day."""
	owner = Owner(
		owner_id="owner-2",
		name="Jordan",
		contact_info="",
		available_minutes_per_day=90,
		preferred_walk_time="evening",
		notification_opt_in=True,
	)
	pet = Pet(
		pet_id="pet-recurring",
		name="Milo",
		species="cat",
		age_years=5,
		weight_kg=4.5,
		medical_notes="",
	)
	owner.add_pet(pet)

	original_due = datetime(2026, 3, 30, 8, 0)
	original_task = Task(
		task_id="daily-feed-1",
		pet_id=pet.pet_id,
		title="Morning feed",
		category="feeding",
		duration_minutes=10,
		priority="medium",
		preferred_window=TimeWindow(start_time=time(7, 0), end_time=time(9, 0)),
		due_by=original_due,
		recurrence="daily",
		requires_owner=True,
	)
	pet.add_task(original_task)

	owner.mark_task_complete(original_task.task_id)

	expected_next_date = (original_due + timedelta(days=1)).date()
	assert any(
		task.task_id != original_task.task_id
		and task.title == original_task.title
		and task.recurrence == "daily"
		and task.due_by is not None
		and task.due_by.date() == expected_next_date
		for task in pet.tasks
	)
