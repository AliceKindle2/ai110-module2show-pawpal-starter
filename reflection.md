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

Yes, one of the changes to the UML was adding the conflict section to the tasks due to it being an important feature to the app in case two tasks conflicted with each other. Also adding more relationships between the classes like pet now having a relationship with tasks like owner does with tasks. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler takes all three into consideration, priority mattering the most since that sets the schedule and duration being the last one to decide when priority fails.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Trade off the scheduler makes is it will consider the higher priority an object has compared to the shortest duration. This makes sense because even if a task takes a shorter amount of time, it shouldn't push back a task with higher priority for the pawpal system. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI, the tool I used being Claude, for writing the code of the system, debugging of the code, and adding everything the phases instructed me to implement into the code. Also refactoring the code so it works properly. The most helpful prompts were the ones that had a clear vision about what should happen and how it should be implemented.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment I did not accept an AI suggestion as-is when I was handling the update to the scheduler in phase 4, the AI seemed to make a mistake after the prompting and made a mistake with the implementation. I saw what AI was doing to the code so I undo the changes and started a new chat with AI, thankfully getting the right results after redoing it. 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

There are 17 tests overall. The behaviors that I test are the statuses of the tasks as they get to completion, adding tests, sorting tasks correctly, logic of the recurrence tasks such as daily and weekly tasks, and tasks that conflict with each other. 

These tests are imoportant due to them making sure the system is working correctly and showing correctly on the app.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

My confidence level for the scheduler working correctly is a level 4. While I trust the AI to make it correctly, I am worried it will look awkward in some points or something was looked over in the design process. 

The edge cases I would have test next would be empty tasks or tasks with a negative input to see how the system would react to it. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with how well the scheduler works over all with the system. It prints out a cohesive and understandable output so early on in the project despite the UML design was fully realized a few prompts before. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I would try to make the app.py, pawpal_system.py, and main.py more streamline so it better flows with the system and works together better. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing about working with AI on this project is make sure you have a clear plan about what you are designing and how it should work overall. That way when you start implementing with AI, you can rein it in to the focus on the project and create the best results due to the focus on the end goal. 