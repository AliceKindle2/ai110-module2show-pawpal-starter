# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

There should be a class called pet with the attributes pet's name, a string. The methods for this section should be edit pet's information, and add pet. This is tied to owner class, which has owner's name that is a string and the methods are edit owner's information. 

Under the class called tasks, there should be methods; see task, add task, edit task, remove task. The attributes for task is a string, along with integers to calculate duration and priorty of the task. 

The last class is the scheduler, which main method is generating the schedule using the tasks. The attribute is the schedule itself. 

The three core actions is add pet, schedule a walk, and see today's tasks. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After creating the skelton of the code, the design of the uml was implemented to establish a relationship with tasks such as "feed pet" to be more connected with each other and establishes the pet's preferences into the tasks. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

the scheduler takes all three into consideration, priority mattering the most since that sets the schedule and duration being the last one to decide when priority fails.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Trade off the scheduler makes is it will consider the higher priority an object has compared to the shortest duration. This makes sense because even if a task takes a shorter amount of time, it shouldn't push back a task with higher priority for the pawpal system. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI, the tool I used being Claude, for writing the code of the system, debugging of the code, and adding everything the phases told me about. Also refactoring the code so it works properly. The most helpful prompts were the ones t

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment I did not accept an AI suggestion as-is when I was handling the 

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
