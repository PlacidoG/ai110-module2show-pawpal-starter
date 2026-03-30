from __future__ import annotations

from datetime import date, datetime, time

from pawpal_system import Owner, Pet, ScheduleEntry, Scheduler, Task, TimeWindow


def build_demo_owner() -> tuple[Owner, Pet]:
	owner = Owner(
		owner_id="owner-1",
		name="Jordan Lee",
		contact_info="jordan@example.com",
		available_minutes_per_day=120,
		preferred_walk_time="morning",
		notification_opt_in=True,
	)

	dog = Pet(
		pet_id="pet-dog-1",
		name="Mochi",
		species="dog",
		age_years=4,
		weight_kg=14.5,
		medical_notes="Mild seasonal allergies.",
		walk_goal_minutes=45,
	)
	cat = Pet(
		pet_id="pet-cat-1",
		name="Luna",
		species="cat",
		age_years=3,
		weight_kg=4.2,
		medical_notes="Sensitive stomach.",
		walk_goal_minutes=0,
	)

	owner.add_pet(dog)
	owner.add_pet(cat)

	today = date.today()

	# At least three tasks with different preferred times across two pets.
	dog.add_task(
		Task(
			task_id="task-001",
			pet_id=dog.pet_id,
			title="Morning walk",
			category="walk",
			duration_minutes=30,
			priority="high",
			preferred_window=TimeWindow(time(7, 0), time(9, 0)),
			due_by=datetime.combine(today, time(9, 30)),
			recurrence="daily",
			requires_owner=True,
		)
	)
	cat.add_task(
		Task(
			task_id="task-002",
			pet_id=cat.pet_id,
			title="Breakfast feeding",
			category="feeding",
			duration_minutes=15,
			priority="high",
			preferred_window=TimeWindow(time(8, 0), time(10, 0)),
			due_by=datetime.combine(today, time(10, 0)),
			recurrence="daily",
			requires_owner=True,
		)
	)
	dog.add_task(
		Task(
			task_id="task-003",
			pet_id=dog.pet_id,
			title="Midday medication",
			category="medication",
			duration_minutes=10,
			priority="high",
			preferred_window=TimeWindow(time(12, 0), time(13, 0)),
			due_by=datetime.combine(today, time(13, 0)),
			recurrence="daily",
			requires_owner=True,
		)
	)
	cat.add_task(
		Task(
			task_id="task-004",
			pet_id=cat.pet_id,
			title="Evening play session",
			category="enrichment",
			duration_minutes=20,
			priority="medium",
			preferred_window=TimeWindow(time(18, 0), time(20, 0)),
			due_by=datetime.combine(today, time(20, 0)),
			recurrence="daily",
			requires_owner=True,
		)
	)

	return owner, dog


def print_todays_schedule(owner: Owner, entries: list[ScheduleEntry]) -> None:
	print("Today's Schedule")
	print("=" * 16)

	if not entries:
		print("No tasks were scheduled today.")
		return

	tasks_by_id = {task.task_id: task for task in owner.get_all_tasks()}
	pet_names_by_id = {pet.pet_id: pet.name for pet in owner.pets}

	for entry in entries:
		task = tasks_by_id.get(entry.task_id)
		task_title = task.title if task else entry.task_id
		pet_name = pet_names_by_id.get(entry.pet_id, entry.pet_id)
		print(
			f"{entry.start_at.strftime('%I:%M %p')} - {entry.end_at.strftime('%I:%M %p')} | "
			f"{pet_name}: {task_title} ({entry.duration_minutes()} min)"
		)


def main() -> None:
	owner, reference_pet = build_demo_owner()
	scheduler = Scheduler(
		strategy="urgency_first",
		max_daily_minutes=180,
		respect_preferences=True,
	)
	day_window = TimeWindow(start_time=time(6, 0), end_time=time(21, 0))

	# Passing an empty task list triggers owner-wide task retrieval in Scheduler.
	plan = scheduler.generate_daily_plan(
		owner=owner,
		pet=reference_pet,
		tasks=[],
		plan_date=date.today(),
		day_window=day_window,
	)

	print_todays_schedule(owner, plan)


if __name__ == "__main__":
	main()
