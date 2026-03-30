from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
	task_id: str
	title: str
	category: str
	duration_minutes: int
	priority: str
	preferred_window: str
	due_by: str
	recurrence: str
	requires_owner: bool
	is_completed: bool = False

	def is_feasible(self, available_minutes: int) -> bool:
		pass

	def mark_completed(self) -> None:
		pass

	def reschedule(self, new_window: str) -> None:
		pass

	def urgency_score(self, current_time: str) -> float:
		pass


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

	def update_health_status(self, activity: str, appetite: str, mood: str) -> None:
		pass

	def add_medication(self, medication: str) -> None:
		pass

	def add_appointment(self, appointment: str) -> None:
		pass

	def get_care_needs(self) -> list[str]:
		pass


@dataclass
class Owner:
	owner_id: str
	name: str
	contact_info: str
	available_minutes_per_day: int
	preferred_walk_time: str
	notification_opt_in: bool
	pets: list[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		pass

	def update_preferences(self, preference: str, value: str) -> None:
		pass

	def set_availability(self, minutes: int) -> None:
		pass

	def mark_task_complete(self, task_id: str) -> None:
		pass

	def view_daily_plan(self, date: str) -> str:
		pass


@dataclass
class Scheduler:
	strategy: str
	max_daily_minutes: int
	respect_preferences: bool

	def generate_daily_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: list[Task],
		date: str,
	) -> list[Task]:
		pass

	def sort_tasks(self, tasks: list[Task]) -> list[Task]:
		pass

	def resolve_conflicts(self, tasks: list[Task], available_minutes: int) -> list[Task]:
		pass

	def explain_plan(self, plan: list[Task], owner: Owner, pet: Pet) -> str:
		pass
