# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
: A user should have the capability to register a pet with an account that contains 
there backround information and administering there daily rountines if they are 
alone. So if a owner is not around there pet, they can use pawpal to track pet care
tasks, schedule a walk and produce a daily plan and explain why it chose that plan


- What classes did you include, and what responsibilities did you assign to each?
: For attrubutes-  A user input personal informatoin about there pet. Information includes 
there Name, species, age, weight,any medical procedures/persciption, future appointments, overall healthn and walk tracker. Overall health means there physcial status, appitite, and mental well being. The app will track there analytics for daily routines. 

- For methods- PawPal can develop a daily plan and explain why it chose that plan for a certain pet. However owners are able to manually change any information that they might pefer for there pet over PawPals suggestions for 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
: Yes, my design changed during implementation when I added explicit task-to-pet relationships and a schedule-entry model with real timestamps instead of only a list of tasks. I made this change so the app could support multiple pets correctly, store daily plans by date, and generate a true calendar-like schedule with clear timing and conflict handling.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
