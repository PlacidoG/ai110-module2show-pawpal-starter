# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
: My initial UML focused on a pet owner creating tasks for one or more pets, then generating a daily plan based on time and priority constraints.


- What classes did you include, and what responsibilities did you assign to each?
: I included `Owner`, `Pet`, `Task`, and `Scheduler`.
: `Owner` manages pets, preferences, completion state, and saved plans.
: `Pet` stores profile/health context and task lists.
: `Task` stores constraints (priority, duration, due time, preferred window, recurrence).
: `Scheduler` ranks, filters, timestamps, and resolves conflicts to generate a daily plan.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
: Yes, my design changed during implementation when I added explicit task-to-pet relationships and a schedule-entry model with real timestamps instead of only a list of tasks. I made this change so the app could support multiple pets correctly, store daily plans by date, and generate a true calendar-like schedule with clear timing and conflict handling.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
: The scheduler considers owner available minutes, scheduler max daily minutes, task duration, preferred time windows, due times, recurrence, completion status, and priority.
- How did you decide which constraints mattered most?
: I prioritized hard constraints first (time windows, non-overlap, minute budget), then urgency scoring (priority + due time + recurrence + owner-required flag) to order feasible tasks.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
: One tradeoff is that tasks are scheduled in a greedy urgency-first order, which is fast and clear but not globally optimal for every possible schedule.
- Why is that tradeoff reasonable for this scenario?
: It is reasonable because this app is a daily planning assistant where speed, explainability, and stable behavior matter more than complex optimization.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
: I used AI to refine class design, improve scheduling flow, add conflict-feedback behavior, and polish UI presentation in Streamlit.
- What kinds of prompts or questions were most helpful?
: Prompts that referenced specific methods and expected behaviors were most helpful, such as asking to surface sorted tasks, filtered tasks, and conflict warnings from scheduler outputs.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
: I did not treat UI-only suggestions as complete; instead, I required scheduler-level conflict feedback (`resolve_conflicts_with_feedback`) so warnings came from actual algorithm results.
- How did you evaluate or verify what the AI suggested?
: I verified by running tests, checking syntax compilation, and confirming the UI displayed sorted, filtered, and conflict rows consistent with scheduler outputs.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
: I tested task completion state changes, adding tasks to pets, chronological/non-overlapping schedule generation, and daily recurrence follow-up creation after completion.
- Why were these tests important?
: These tests cover core correctness for scheduling, data integrity, and recurrence behavior, which are the highest-risk parts of the system.

**b. Confidence**

- How confident are you that your scheduler works correctly?
: I am confident (about 4/5) that the scheduler works correctly for normal daily planning scenarios.
- What edge cases would you test next if you had more time?
: I would test overnight windows crossing midnight, equal urgency ties, very tight minute budgets, weekly recurrence over many cycles, and multi-pet fairness when many tasks compete for limited time.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
: I am most satisfied with integrating backend scheduling logic and a professional UI that explains sorted tasks, filtered tasks, and conflict warnings clearly.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
: I would improve editing/deleting tasks in the UI, add stronger preference controls, and explore a more advanced optimization strategy beyond greedy urgency-first scheduling.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
: I learned that AI is most useful when requirements are specific, but final quality still depends on human judgment, testing, and validating behavior against real constraints.
