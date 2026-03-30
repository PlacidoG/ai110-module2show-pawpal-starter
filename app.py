from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

from main import build_demo_owner
from pawpal_system import Owner, Pet, ScheduleEntry, Scheduler, Task, TimeWindow


def _safe_id(raw_value: str, prefix: str) -> str:
    """Create a stable ID slug from free text input."""
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in raw_value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        cleaned = prefix
    return f"{prefix}-{cleaned}"


def _ensure_vault() -> dict[str, dict[str, object]]:
    """Create and normalize the session vault used for shared objects."""
    if "vault" not in st.session_state:
        st.session_state.vault = {
            "owners": {},
            "pets": {},
            "schedulers": {},
        }

    vault = st.session_state.vault
    vault.setdefault("owners", {})
    vault.setdefault("pets", {})
    vault.setdefault("schedulers", {})
    return vault


def _get_or_create_owner(vault: dict[str, dict[str, object]], owner_name: str) -> tuple[Owner, bool]:
    """Reuse an owner from session vault if present; otherwise create one."""
    owner_id = _safe_id(owner_name, "owner")
    existing_owner = vault["owners"].get(owner_id)
    if isinstance(existing_owner, Owner):
        if owner_name.strip():
            existing_owner.name = owner_name.strip()
        return existing_owner, False

    new_owner = Owner(
        owner_id=owner_id,
        name=owner_name.strip() or "Owner",
        contact_info="",
        available_minutes_per_day=120,
        preferred_walk_time="morning",
        notification_opt_in=True,
    )
    vault["owners"][owner_id] = new_owner
    return new_owner, True


def _get_active_owner(vault: dict[str, dict[str, object]]) -> Owner | None:
    """Return the currently selected owner from session state."""
    owner_id = st.session_state.get("active_owner_id", "")
    candidate = vault["owners"].get(owner_id)
    if isinstance(candidate, Owner):
        return candidate
    return None


def _pet_label(owner: Owner, pet_id: str) -> str:
    """Return a user-friendly label for a pet ID."""
    for pet in owner.pets:
        if pet.pet_id == pet_id:
            return f"{pet.name} ({pet.species})"
    return pet_id


def _get_pet_by_id(owner: Owner, pet_id: str) -> Pet | None:
    """Find a pet by ID in the active owner profile."""
    for pet in owner.pets:
        if pet.pet_id == pet_id:
            return pet
    return None


def _add_or_update_pet(
    vault: dict[str, dict[str, object]],
    owner: Owner,
    pet_name: str,
    species: str,
    age_years: int,
    weight_kg: float,
    medical_notes: str,
    walk_goal_minutes: int,
) -> tuple[Pet, bool]:
    """Use Owner.add_pet for new pets and update existing pets by stable ID."""
    pet_id = f"{owner.owner_id}:{_safe_id(pet_name, 'pet')}"
    existing_pet = _get_pet_by_id(owner, pet_id)

    if existing_pet is not None:
        existing_pet.name = pet_name.strip() or existing_pet.name
        existing_pet.species = species
        existing_pet.age_years = age_years
        existing_pet.weight_kg = weight_kg
        existing_pet.medical_notes = medical_notes
        existing_pet.walk_goal_minutes = walk_goal_minutes
        vault["pets"][existing_pet.pet_id] = existing_pet
        return existing_pet, False

    new_pet = Pet(
        pet_id=pet_id,
        name=pet_name.strip(),
        species=species,
        age_years=age_years,
        weight_kg=weight_kg,
        medical_notes=medical_notes,
        walk_goal_minutes=walk_goal_minutes,
    )
    owner.add_pet(new_pet)
    vault["pets"][new_pet.pet_id] = new_pet
    return new_pet, True


def _get_or_create_scheduler(vault: dict[str, dict[str, object]]) -> tuple[Scheduler, bool]:
    """Reuse a scheduler instance from session vault if present."""
    scheduler_key = "default"
    existing_scheduler = vault["schedulers"].get(scheduler_key)
    if isinstance(existing_scheduler, Scheduler):
        return existing_scheduler, False

    new_scheduler = Scheduler(
        strategy="urgency-first",
        max_daily_minutes=180,
        respect_preferences=True,
    )
    vault["schedulers"][scheduler_key] = new_scheduler
    return new_scheduler, True


def _categorize_task(title: str) -> str:
    """Infer a basic category from the task title for demo scheduling."""
    lowered = title.lower()
    if "walk" in lowered:
        return "walk"
    if "feed" in lowered or "meal" in lowered:
        return "feeding"
    if "med" in lowered:
        return "medication"
    return "care"


def _add_task_to_pet(
    pet: Pet,
    task_id: str,
    title: str,
    duration_minutes: int,
    priority: str,
    recurrence: str,
    preferred_start: time,
    preferred_end: time,
    due_time: time,
    requires_owner: bool,
) -> tuple[Task, bool]:
    """Create a Task and insert it through Pet.add_task to enforce uniqueness."""
    new_task = Task(
        task_id=task_id,
        pet_id=pet.pet_id,
        title=title.strip(),
        category=_categorize_task(title),
        duration_minutes=max(1, int(duration_minutes)),
        priority=priority,
        preferred_window=TimeWindow(start_time=preferred_start, end_time=preferred_end),
        due_by=datetime.combine(date.today(), due_time),
        recurrence=recurrence,
        requires_owner=requires_owner,
    )

    before_count = len(pet.tasks)
    pet.add_task(new_task)
    return new_task, len(pet.tasks) > before_count


def _schedule_rows(plan: list[ScheduleEntry], owner: Owner) -> list[dict[str, str | int]]:
    """Convert schedule entries to a table-friendly row structure."""
    tasks_by_id = {task.task_id: task for task in owner.get_all_tasks()}
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}
    rows: list[dict[str, str | int]] = []

    for entry in plan:
        task = tasks_by_id.get(entry.task_id)
        rows.append(
            {
                "start": entry.start_at.strftime("%I:%M %p"),
                "end": entry.end_at.strftime("%I:%M %p"),
                "pet": pet_names.get(entry.pet_id, entry.pet_id),
                "task": task.title if task else entry.task_id,
                "minutes": entry.duration_minutes(),
            }
        )
    return rows


def _pet_rows(owner: Owner) -> list[dict[str, str | int | float]]:
    """Convert pet models to a table-friendly row structure."""
    return [
        {
            "pet_id": pet.pet_id,
            "name": pet.name,
            "species": pet.species,
            "age_years": pet.age_years,
            "weight_kg": pet.weight_kg,
            "tasks": len(pet.tasks),
        }
        for pet in owner.pets
    ]


def _task_rows(pet: Pet) -> list[dict[str, str | int]]:
    """Convert task models to a table-friendly row structure."""
    return [
        {
            "task_id": task.task_id,
            "title": task.title,
            "priority": task.priority,
            "duration_minutes": task.duration_minutes,
            "recurrence": task.recurrence,
        }
        for task in pet.tasks
    ]


def _window_label(window: TimeWindow | None) -> str:
    """Format an optional time window for display in tables."""
    if window is None:
        return "Any time"
    return f"{window.start_time.strftime('%I:%M %p')} - {window.end_time.strftime('%I:%M %p')}"


def _sorted_task_rows(tasks: list[Task], owner: Owner, score_time: datetime) -> list[dict[str, str | int | float]]:
    """Convert sorted tasks to rows that show scheduler urgency decisions."""
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}
    rows: list[dict[str, str | int | float]] = []
    for task in tasks:
        rows.append(
            {
                "task": task.title,
                "pet": pet_names.get(task.pet_id, task.pet_id),
                "priority": task.priority,
                "urgency_score": round(task.urgency_score(score_time), 2),
                "duration_minutes": task.duration_minutes,
                "preferred_window": _window_label(task.preferred_window),
                "due_by": task.due_by.strftime("%I:%M %p") if task.due_by else "No due time",
            }
        )
    return rows


def _filtered_task_rows(
    tasks: list[Task],
    owner: Owner,
    available_minutes: int,
    day_window: TimeWindow,
) -> list[dict[str, str | int]]:
    """Convert filtered tasks to rows explaining why they were skipped."""
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}
    rows: list[dict[str, str | int]] = []

    for task in tasks:
        if task.task_id in owner.completed_task_ids or task.is_completed:
            reason = "Already completed"
        elif task.duration_minutes > available_minutes:
            reason = "Duration exceeds available minutes"
        elif task.preferred_window is not None and not task.preferred_window.overlaps(day_window):
            reason = "Preferred window is outside day bounds"
        else:
            reason = "Filtered by scheduler constraints"

        rows.append(
            {
                "task": task.title,
                "pet": pet_names.get(task.pet_id, task.pet_id),
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "reason": reason,
            }
        )

    return rows


def _conflict_rows(entries: list[ScheduleEntry], owner: Owner) -> list[dict[str, str | int]]:
    """Convert dropped schedule entries into warning rows for owners."""
    tasks_by_id = {task.task_id: task for task in owner.get_all_tasks()}
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}
    rows: list[dict[str, str | int]] = []

    for entry in entries:
        task = tasks_by_id.get(entry.task_id)
        rows.append(
            {
                "task": task.title if task else entry.task_id,
                "pet": pet_names.get(entry.pet_id, entry.pet_id),
                "start": entry.start_at.strftime("%I:%M %p"),
                "end": entry.end_at.strftime("%I:%M %p"),
                "minutes": entry.duration_minutes(),
                "status": "Held for conflict or time cap",
            }
        )

    return rows

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

vault = _ensure_vault()

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

if "active_owner_id" not in st.session_state:
    default_owner, _ = _get_or_create_owner(vault, "Jordan")
    st.session_state.active_owner_id = default_owner.owner_id

if "owner_name_input" not in st.session_state:
    current_owner = _get_active_owner(vault)
    st.session_state.owner_name_input = current_owner.name if current_owner else "Jordan"

if "active_pet_id" not in st.session_state:
    st.session_state.active_pet_id = ""

st.title("🐾 PawPal+")

st.markdown("Use this UI to add pets, schedule tasks, and generate a daily plan with your existing classes.")

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", key="owner_name_input")
col_owner_1, col_owner_2 = st.columns(2)

with col_owner_1:
    if st.button("Use this owner"):
        owner, owner_created = _get_or_create_owner(vault, owner_name)
        st.session_state.active_owner_id = owner.owner_id
        if owner_created:
            st.success(f"Created owner profile for {owner.name}.")
        else:
            st.info(f"Using existing owner profile for {owner.name}.")

with col_owner_2:
    if st.button("Load demo owner from main.py"):
        demo_owner, reference_pet = build_demo_owner()
        vault["owners"][demo_owner.owner_id] = demo_owner
        for demo_pet in demo_owner.pets:
            vault["pets"][demo_pet.pet_id] = demo_pet
        st.session_state.active_owner_id = demo_owner.owner_id
        st.session_state.owner_name_input = demo_owner.name
        st.session_state.active_pet_id = reference_pet.pet_id
        st.success("Loaded demo owner, pets, and tasks from main.py.")

active_owner = _get_active_owner(vault)
if active_owner is None:
    active_owner, _ = _get_or_create_owner(vault, owner_name)
    st.session_state.active_owner_id = active_owner.owner_id

st.caption(f"Active owner: {active_owner.name} | Pets: {len(active_owner.pets)}")

st.subheader("Add a Pet")
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    col_pet_1, col_pet_2 = st.columns(2)
    with col_pet_1:
        age_years = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
        walk_goal_minutes = st.number_input("Walk goal (minutes)", min_value=0, max_value=240, value=30)
    with col_pet_2:
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=120.0, value=5.0, step=0.1)
    medical_notes = st.text_area("Medical notes", value="")
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if not pet_name.strip():
        st.error("Pet name is required.")
    else:
        pet, was_created = _add_or_update_pet(
            vault=vault,
            owner=active_owner,
            pet_name=pet_name,
            species=species,
            age_years=int(age_years),
            weight_kg=float(weight_kg),
            medical_notes=medical_notes,
            walk_goal_minutes=int(walk_goal_minutes),
        )
        st.session_state.active_pet_id = pet.pet_id
        if was_created:
            st.success(f"Added pet {pet.name} using Owner.add_pet.")
        else:
            st.info(f"Pet {pet.name} already existed. Profile updated.")

if active_owner.pets:
    st.write("Current pets:")
    st.table(_pet_rows(active_owner))
else:
    st.info("No pets yet. Add one using the form above.")

st.subheader("Schedule a Task")
if not active_owner.pets:
    st.info("Add at least one pet before creating tasks.")
else:
    pet_ids = [pet.pet_id for pet in active_owner.pets]
    if st.session_state.active_pet_id not in pet_ids:
        st.session_state.active_pet_id = pet_ids[0]

    selected_pet_id = st.selectbox(
        "Pet",
        options=pet_ids,
        key="active_pet_id",
        format_func=lambda pet_id: _pet_label(active_owner, pet_id),
    )
    selected_pet = _get_pet_by_id(active_owner, selected_pet_id)

    with st.form("add_task_form", clear_on_submit=True):
        task_title = st.text_input("Task title")
        col_task_1, col_task_2 = st.columns(2)
        with col_task_1:
            duration_minutes = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
            recurrence = st.selectbox("Recurrence", ["once", "daily", "weekly"], index=0)
        with col_task_2:
            preferred_start = st.time_input("Preferred start", value=time(8, 0))
            preferred_end = st.time_input("Preferred end", value=time(10, 0))
            due_time = st.time_input("Due by", value=time(20, 0))
            requires_owner = st.checkbox("Requires owner", value=True)

        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted and selected_pet is not None:
        if not task_title.strip():
            st.error("Task title is required.")
        else:
            st.session_state.task_counter += 1
            next_task_id = f"{selected_pet.pet_id}-task-{st.session_state.task_counter}"
            task, task_added = _add_task_to_pet(
                pet=selected_pet,
                task_id=next_task_id,
                title=task_title,
                duration_minutes=int(duration_minutes),
                priority=priority,
                recurrence=recurrence,
                preferred_start=preferred_start,
                preferred_end=preferred_end,
                due_time=due_time,
                requires_owner=requires_owner,
            )

            if task_added:
                st.success(f"Added task {task.title} using Pet.add_task.")
            else:
                st.warning("Task was not added because the task ID already exists.")

    if selected_pet is not None and selected_pet.tasks:
        st.write(f"Tasks for {selected_pet.name}:")
        st.table(_task_rows(selected_pet))
    elif selected_pet is not None:
        st.info(f"No tasks yet for {selected_pet.name}.")

st.divider()

st.subheader("Build Schedule")

if not active_owner.pets:
    st.info("Add a pet and at least one task before generating a schedule.")
else:
    col_plan_1, col_plan_2 = st.columns(2)
    with col_plan_1:
        plan_date = st.date_input("Plan date", value=date.today())
        day_start = st.time_input("Day start", value=time(6, 0))
    with col_plan_2:
        available_minutes = st.number_input(
            "Owner available minutes",
            min_value=0,
            max_value=600,
            value=active_owner.available_minutes_per_day,
            step=5,
        )
        day_end = st.time_input("Day end", value=time(22, 0))

    active_owner.set_availability(int(available_minutes))

    if st.button("Generate schedule"):
        scheduler, scheduler_created = _get_or_create_scheduler(vault)
        reference_pet = active_owner.pets[0]

        day_window = TimeWindow(start_time=day_start, end_time=day_end)
        scheduler_minutes = min(active_owner.available_minutes_per_day, scheduler.max_daily_minutes)
        candidate_tasks = scheduler.get_tasks_for_owner(active_owner)
        feasible_tasks = [
            task
            for task in candidate_tasks
            if task.task_id not in active_owner.completed_task_ids
            and task.is_feasible(scheduler_minutes, day_window)
        ]
        feasible_task_ids = {task.task_id for task in feasible_tasks}
        filtered_tasks = [task for task in candidate_tasks if task.task_id not in feasible_task_ids]

        score_time = datetime.combine(plan_date, day_window.start_time)
        sorted_tasks = scheduler.sort_tasks(feasible_tasks, score_time)
        tentative_entries = scheduler.assign_timestamps(sorted_tasks, plan_date, day_window)
        _, dropped_entries = scheduler.resolve_conflicts_with_feedback(
            tentative_entries,
            scheduler_minutes,
        )

        plan = scheduler.generate_daily_plan(
            owner=active_owner,
            pet=reference_pet,
            tasks=feasible_tasks,
            plan_date=plan_date,
            day_window=day_window,
        )

        st.session_state.latest_plan = plan
        st.session_state.latest_plan_owner_id = active_owner.owner_id
        st.session_state.latest_sorted_rows = _sorted_task_rows(sorted_tasks, active_owner, score_time)
        st.session_state.latest_filtered_rows = _filtered_task_rows(
            filtered_tasks,
            active_owner,
            scheduler_minutes,
            day_window,
        )
        st.session_state.latest_conflict_rows = _conflict_rows(dropped_entries, active_owner)
        st.session_state.latest_scheduler_minutes = scheduler_minutes
        st.session_state.latest_scheduler_cap = scheduler.max_daily_minutes
        if scheduler_created:
            st.info("Created scheduler in session vault.")
        else:
            st.info("Reused scheduler from session vault.")

    latest_plan = st.session_state.get("latest_plan", [])
    latest_plan_owner_id = st.session_state.get("latest_plan_owner_id", "")
    latest_sorted_rows = st.session_state.get("latest_sorted_rows", [])
    latest_filtered_rows = st.session_state.get("latest_filtered_rows", [])
    latest_conflict_rows = st.session_state.get("latest_conflict_rows", [])
    latest_scheduler_minutes = st.session_state.get("latest_scheduler_minutes", 0)
    latest_scheduler_cap = st.session_state.get("latest_scheduler_cap", 0)

    if latest_plan_owner_id == active_owner.owner_id:
        scheduler, _ = _get_or_create_scheduler(vault)

        if latest_scheduler_minutes < int(available_minutes):
            st.info(
                f"Scheduler used {latest_scheduler_minutes} minutes because its max_daily_minutes "
                f"setting is {latest_scheduler_cap}."
            )

        if latest_sorted_rows:
            st.success(f"Sorted {len(latest_sorted_rows)} feasible task(s) by scheduler urgency.")
            st.table(latest_sorted_rows)

        if latest_filtered_rows:
            st.warning(
                f"Filtered out {len(latest_filtered_rows)} task(s) that did not meet today's constraints."
            )
            st.table(latest_filtered_rows)

        if latest_conflict_rows:
            st.warning(
                "🔵🐶 PawPal conflict alert: some tentative tasks overlapped or exceeded today's "
                "time budget. Try widening preferred windows or increasing available minutes."
            )
            st.table(latest_conflict_rows)
        elif latest_sorted_rows:
            st.success("No task conflicts were flagged by the scheduler.")

        if latest_plan:
            st.success(f"Generated {len(latest_plan)} scheduled task(s).")
            st.table(_schedule_rows(latest_plan, active_owner))
        else:
            st.warning("No tasks could be scheduled with the current constraints.")

        st.markdown(scheduler.explain_plan(latest_plan, active_owner, active_owner.pets[0]))
