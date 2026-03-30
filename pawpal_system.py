from __future__ import annotations

from datetime import date, datetime, time, timedelta
from dataclasses import dataclass, field


@dataclass
class TimeWindow:
	start_time: time
	end_time: time

	def contains(self, value: time) -> bool:
		"""Return True when the given time falls within this window."""
		if self.start_time <= self.end_time:
			return self.start_time <= value <= self.end_time
		return value >= self.start_time or value <= self.end_time

	def overlaps(self, other: TimeWindow) -> bool:
		"""Return True when this window intersects with another window."""
		def _to_segments(window: TimeWindow) -> list[tuple[time, time]]:
			if window.start_time <= window.end_time:
				return [(window.start_time, window.end_time)]
			return [(window.start_time, time.max), (time.min, window.end_time)]

		for start_a, end_a in _to_segments(self):
			for start_b, end_b in _to_segments(other):
				if start_a <= end_b and start_b <= end_a:
					return True
		return False


@dataclass
class ScheduleEntry:
	entry_id: str
	task_id: str
	pet_id: str
	start_at: datetime
	end_at: datetime
	status: str = "scheduled"
	reason: str = ""

	def overlaps_with(self, other: ScheduleEntry) -> bool:
		"""Return True when two scheduled entries overlap in time."""
		return self.start_at < other.end_at and other.start_at < self.end_at

	def duration_minutes(self) -> int:
		"""Return the entry duration in whole minutes."""
		return max(0, int((self.end_at - self.start_at).total_seconds() // 60))


@dataclass
class Task:
	task_id: str
	pet_id: str
	title: str
	category: str
	duration_minutes: int
	priority: str
	preferred_window: TimeWindow | None
	due_by: datetime | None
	recurrence: str
	requires_owner: bool
	is_completed: bool = False

	def is_feasible(self, available_minutes: int, available_window: TimeWindow) -> bool:
		"""Return whether this task can fit the available time and window."""
		if self.is_completed:
			return False
		if self.duration_minutes > available_minutes:
			return False
		if self.preferred_window is None:
			return True
		return self.preferred_window.overlaps(available_window)

	def mark_completed(self) -> None:
		"""Mark this task as completed."""
		self.is_completed = True

	def reschedule(self, new_window: TimeWindow) -> None:
		"""Update the preferred time window for this task."""
		self.preferred_window = new_window

	def urgency_score(self, current_time: datetime) -> float:
		"""Calculate a score used to prioritize this task for scheduling."""
		if self.is_completed:
			return 0.0

		priority_weight = {
			"high": 3.0,
			"medium": 2.0,
			"low": 1.0,
		}
		score = priority_weight.get(self.priority.lower(), 1.5)

		if self.due_by is not None:
			minutes_until_due = (self.due_by - current_time).total_seconds() / 60
			if minutes_until_due <= 0:
				score += 4.0
			elif minutes_until_due <= 120:
				score += 3.0
			elif minutes_until_due <= 480:
				score += 2.0
			elif minutes_until_due <= 1440:
				score += 1.0

		recurrence_weight = {
			"once": 0.0,
			"daily": 0.75,
			"weekly": 0.25,
		}
		score += recurrence_weight.get(self.recurrence.lower(), 0.5)

		if self.requires_owner:
			score += 0.25

		return score


@dataclass
class Pet:
	pet_id: str
	name: str
	species: str
	age_years: int
	weight_kg: float
	medical_notes: str
	medications: list[str] = field(default_factory=list)
	appointments: list[str] = field(default_factory=list)
	activity_level: str = ""
	appetite_status: str = ""
	mood_status: str = ""
	walk_goal_minutes: int = 0
	tasks: list[Task] = field(default_factory=list)

	def update_health_status(self, activity: str, appetite: str, mood: str) -> None:
		"""Normalize and store the pet's latest health status indicators."""
		self.activity_level = activity.strip().lower()
		self.appetite_status = appetite.strip().lower()
		self.mood_status = mood.strip().lower()

	def add_medication(self, medication: str) -> None:
		"""Add a medication reminder if it is non-empty and not duplicated."""
		value = medication.strip()
		if value and value not in self.medications:
			self.medications.append(value)

	def add_appointment(self, appointment: str) -> None:
		"""Add an appointment note if it is non-empty and not duplicated."""
		value = appointment.strip()
		if value and value not in self.appointments:
			self.appointments.append(value)

	def add_task(self, task: Task) -> None:
		"""Attach a task to this pet when IDs match and task is unique."""
		if task.pet_id != self.pet_id:
			raise ValueError("Task pet_id must match this pet")
		if any(existing.task_id == task.task_id for existing in self.tasks):
			return
		self.tasks.append(task)

	def remove_task(self, task_id: str) -> None:
		"""Remove all tasks matching the provided task ID."""
		self.tasks = [task for task in self.tasks if task.task_id != task_id]

	def get_care_needs(self) -> list[str]:
		"""Summarize outstanding care needs based on current pet state."""
		needs: list[str] = []

		if self.medical_notes.strip():
			needs.append("Review medical notes and monitor symptoms.")

		if self.medications:
			needs.append(f"{len(self.medications)} medication reminder(s) needed.")

		if self.appointments:
			needs.append(f"{len(self.appointments)} upcoming appointment(s).")

		pending_tasks = [task for task in self.tasks if not task.is_completed]
		if pending_tasks:
			needs.append(f"{len(pending_tasks)} care task(s) still pending.")

		completed_walk_minutes = sum(
			task.duration_minutes
			for task in self.tasks
			if task.is_completed and task.category.lower() == "walk"
		)
		remaining_walk = max(0, self.walk_goal_minutes - completed_walk_minutes)
		if remaining_walk > 0:
			needs.append(f"{remaining_walk} walk minute(s) remaining for today's goal.")

		if self.activity_level in {"low", "lethargic"}:
			needs.append("Low activity observed; add enrichment or a gentle walk.")

		if self.appetite_status in {"low", "poor"}:
			needs.append("Low appetite observed; monitor food and hydration.")

		if self.mood_status in {"anxious", "stressed", "sad"}:
			needs.append("Mood suggests stress; include calming activities.")

		return needs


@dataclass
class Owner:
	owner_id: str
	name: str
	contact_info: str
	available_minutes_per_day: int
	preferred_walk_time: str
	notification_opt_in: bool
	pets: list[Pet] = field(default_factory=list)
	completed_task_ids: set[str] = field(default_factory=set)
	daily_plans_by_date: dict[date, list[ScheduleEntry]] = field(default_factory=dict)

	def add_pet(self, pet: Pet) -> None:
		"""Add a pet to this owner if it has not already been added."""
		if any(existing.pet_id == pet.pet_id for existing in self.pets):
			return
		self.pets.append(pet)

	def update_preferences(self, preference: str, value: str) -> None:
		"""Update an owner preference value by preference key."""
		key = preference.strip().lower()
		if key == "preferred_walk_time":
			self.preferred_walk_time = value
		elif key == "contact_info":
			self.contact_info = value
		elif key == "notification_opt_in":
			self.notification_opt_in = value.strip().lower() in {"true", "1", "yes", "on"}
		elif key == "available_minutes_per_day":
			self.set_availability(int(value))
		else:
			raise ValueError(f"Unknown preference: {preference}")

	def set_availability(self, minutes: int) -> None:
		"""Set available care minutes per day, rejecting negative values."""
		if minutes < 0:
			raise ValueError("Availability cannot be negative")
		self.available_minutes_per_day = minutes

	def _next_due_for_recurrence(self, task: Task) -> datetime | None:
		"""Return the next due datetime for recurring tasks when available."""
		if task.due_by is None:
			return None

		recurrence = task.recurrence.strip().lower()
		if recurrence == "daily":
			return task.due_by + timedelta(days=1)
		if recurrence == "weekly":
			return task.due_by + timedelta(days=7)
		return None

	def _build_follow_up_task_id(self, pet: Pet, source_task: Task, next_due: datetime | None) -> str:
		"""Build a unique follow-up task ID derived from the source task."""
		suffix = next_due.strftime("%Y%m%d") if next_due is not None else "next"
		base_id = f"{source_task.task_id}-next-{suffix}"
		existing_ids = {task.task_id for task in pet.tasks}
		if base_id not in existing_ids:
			return base_id

		counter = 2
		candidate_id = f"{base_id}-{counter}"
		while candidate_id in existing_ids:
			counter += 1
			candidate_id = f"{base_id}-{counter}"
		return candidate_id

	def _create_recurring_follow_up(self, pet: Pet, task: Task) -> None:
		"""Create the next task instance for daily/weekly recurring tasks."""
		recurrence = task.recurrence.strip().lower()
		if recurrence not in {"daily", "weekly"}:
			return

		next_due = self._next_due_for_recurrence(task)
		new_task_id = self._build_follow_up_task_id(pet, task, next_due)

		next_window = None
		if task.preferred_window is not None:
			next_window = TimeWindow(
				start_time=task.preferred_window.start_time,
				end_time=task.preferred_window.end_time,
			)

		pet.add_task(
			Task(
				task_id=new_task_id,
				pet_id=task.pet_id,
				title=task.title,
				category=task.category,
				duration_minutes=task.duration_minutes,
				priority=task.priority,
				preferred_window=next_window,
				due_by=next_due,
				recurrence=task.recurrence,
				requires_owner=task.requires_owner,
			)
		)

	def mark_task_complete(self, task_id: str) -> None:
		"""Mark a task complete and create a follow-up when it recurs."""
		if task_id in self.completed_task_ids:
			return

		self.completed_task_ids.add(task_id)
		for pet in self.pets:
			for task in pet.tasks:
				if task.task_id == task_id:
					task.mark_completed()
					self._create_recurring_follow_up(pet, task)
					return

	def store_daily_plan(self, plan_date: date, entries: list[ScheduleEntry]) -> None:
		"""Store a day's schedule entries sorted by start time."""
		self.daily_plans_by_date[plan_date] = sorted(entries, key=lambda entry: entry.start_at)

	def view_daily_plan(self, plan_date: date) -> list[ScheduleEntry]:
		"""Return the saved schedule entries for a given date."""
		return list(self.daily_plans_by_date.get(plan_date, []))

	def get_all_tasks(self) -> list[Task]:
		"""Return a flat list of tasks from all owned pets."""
		all_tasks: list[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.tasks)
		return all_tasks


@dataclass
class Scheduler:
	strategy: str
	max_daily_minutes: int
	respect_preferences: bool

	def get_tasks_for_owner(self, owner: Owner, pet_id: str | None = None) -> list[Task]:
		"""Return owner tasks, optionally filtered to a specific pet ID."""
		tasks = owner.get_all_tasks()
		if pet_id is None:
			return tasks
		return [task for task in tasks if task.pet_id == pet_id]

	def _window_bounds(self, plan_date: date, window: TimeWindow) -> tuple[datetime, datetime]:
		"""Convert a window on a date into concrete datetime bounds."""
		start_at = datetime.combine(plan_date, window.start_time)
		end_at = datetime.combine(plan_date, window.end_time)
		if end_at <= start_at:
			end_at += timedelta(days=1)
		return start_at, end_at

	def generate_daily_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: list[Task],
		plan_date: date,
		day_window: TimeWindow,
	) -> list[ScheduleEntry]:
		"""Build and store a conflict-free daily schedule for the owner."""
		available_minutes = min(owner.available_minutes_per_day, self.max_daily_minutes)
		if available_minutes <= 0:
			owner.store_daily_plan(plan_date, [])
			return []

		candidate_tasks = list(tasks) if tasks else self.get_tasks_for_owner(owner)

		feasible_tasks = [
			task
			for task in candidate_tasks
			if task.task_id not in owner.completed_task_ids
			and task.is_feasible(available_minutes, day_window)
		]

		sorted_tasks = self.sort_tasks(
			feasible_tasks,
			datetime.combine(plan_date, day_window.start_time),
		)
		tentative_entries = self.assign_timestamps(sorted_tasks, plan_date, day_window)
		resolved_entries = self.resolve_conflicts(tentative_entries, available_minutes)

		owner.store_daily_plan(plan_date, resolved_entries)
		return resolved_entries

	def sort_tasks(self, tasks: list[Task], current_time: datetime) -> list[Task]:
		"""Sort tasks from highest to lowest urgency score."""
		return sorted(tasks, key=lambda task: task.urgency_score(current_time), reverse=True)

	def assign_timestamps(
		self,
		tasks: list[Task],
		plan_date: date,
		day_window: TimeWindow,
	) -> list[ScheduleEntry]:
		"""Assign tentative start and end times to tasks within window bounds."""
		entries: list[ScheduleEntry] = []
		day_start, day_end = self._window_bounds(plan_date, day_window)
		cursor = day_start

		for task in tasks:
			task_window = task.preferred_window or day_window
			task_start_bound, task_end_bound = self._window_bounds(plan_date, task_window)

			if task_start_bound < day_start:
				task_start_bound = day_start
			if task_end_bound > day_end:
				task_end_bound = day_end

			if task_end_bound <= task_start_bound:
				continue

			start_at = max(cursor, task_start_bound)
			end_at = start_at + timedelta(minutes=task.duration_minutes)
			if end_at > task_end_bound or end_at > day_end:
				continue

			entries.append(
				ScheduleEntry(
					entry_id=f"{task.task_id}-{start_at.strftime('%Y%m%d%H%M')}",
					task_id=task.task_id,
					pet_id=task.pet_id,
					start_at=start_at,
					end_at=end_at,
					reason=f"Selected for urgency score {task.urgency_score(day_start):.2f}.",
				)
			)
			cursor = end_at

			if cursor >= day_end:
				break

		return entries

	def resolve_conflicts(
		self,
		entries: list[ScheduleEntry],
		available_minutes: int,
	) -> list[ScheduleEntry]:
		"""Filter entries to remove overlaps and enforce daily minute limits."""
		resolved, _ = self.resolve_conflicts_with_feedback(entries, available_minutes)
		return resolved

	def resolve_conflicts_with_feedback(
		self,
		entries: list[ScheduleEntry],
		available_minutes: int,
	) -> tuple[list[ScheduleEntry], list[ScheduleEntry]]:
		"""Return scheduled entries and entries dropped for time/conflict constraints."""
		if available_minutes <= 0:
			return [], list(entries)

		resolved: list[ScheduleEntry] = []
		dropped: list[ScheduleEntry] = []
		used_minutes = 0

		for entry in sorted(entries, key=lambda item: item.start_at):
			entry_minutes = entry.duration_minutes()
			if used_minutes + entry_minutes > available_minutes:
				dropped.append(entry)
				continue
			if resolved and entry.overlaps_with(resolved[-1]):
				dropped.append(entry)
				continue

			resolved.append(entry)
			used_minutes += entry_minutes

		return resolved, dropped

	def explain_plan(self, plan: list[ScheduleEntry], owner: Owner, pet: Pet) -> str:
		"""Return a human-readable explanation of the generated plan."""
		if not plan:
			return "No tasks were scheduled today."

		tasks_by_id = {task.task_id: task for task in owner.get_all_tasks()}
		pet_names_by_id = {owned_pet.pet_id: owned_pet.name for owned_pet in owner.pets}
		planned_pet_ids = {entry.pet_id for entry in plan}
		if len(planned_pet_ids) == 1:
			planned_pet_id = next(iter(planned_pet_ids))
			plan_label = pet_names_by_id.get(planned_pet_id, pet.name)
			lines = [f"Daily plan for {plan_label}:"]
		else:
			lines = [f"Daily plan for all pets owned by {owner.name}:"]

		for entry in plan:
			task = tasks_by_id.get(entry.task_id)
			task_title = task.title if task else entry.task_id
			pet_name = pet_names_by_id.get(entry.pet_id, entry.pet_id)
			lines.append(
				f"- {entry.start_at.strftime('%I:%M %p')} to {entry.end_at.strftime('%I:%M %p')}: "
				f"{task_title} for {pet_name} ({entry.duration_minutes()} min)"
			)
		return "\n".join(lines)
