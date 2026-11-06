# Grant proposal draft

## 1. You

I have been a UX designer for 15 years, and have worked in all sorts of tech companies, from a 10 person company to being on a ux team of 64 designers and researchers. The one thing that has been consistent is that being a good communicator is the most important skill you can have

Early in my career so much of the social dynamics of the workplace was confusing to me and I wasted a lot of energy managing communications with others. I was not the only one that experienced this challenge either. One developer who I worked with closely simply did not understand how to communicate his ideas to others, and often came across as difficult, and yet they were an extremely effective and hard working member of the team. However this did not prevent them from being fired for their style of communication

The reason that I am passionate about this problem is that I think modern day tech companies are dehumanizing to work for, every piece of corporate software is focused on tracking and monitoring and trying to get the most out of each of its employees rather than being focused on the well being of those workers.

As a Senior User Experience Designer, my job is to understand what people need in order to accomplish a goal through technology, which is exactly the skill workplace conflict resolution requires. That's why I'm building Mend.

## 2. The mainstream view you agree with

I believe like most companies do, that the best way to handle conflict in the workplace is to keep it to yourself. Don't bring coworkers into the situation because they won't help resolve the problem and then you are wasting their time not just yours. You should also not go to HR with these problems, because all that HR sees is someone coming to them and creating a problem where one didn't exist yesterday (to them because they were not aware and therefore it didn't exist in their world)

## 3. The idea

**Problem**

Currently when you experience conflict in the work place there are no good options to handle it with you can just keep it to yourself unresolved, take it to a friendly coworker and get validation but no solution to how to handle the conflict. Or you can bring it to HR which then means the solution and consequences are no longer in your hands

Currently conflict in the workplace is responsible on average for over 2 hours a week of employees time handling it (CPP, Inc., *Workplace Conflict and How Businesses Can Harness It to Thrive*, 2008, found 2.8 hrs/week; a 2022 Myers-Briggs Company follow-up, different methodology, found 4.34 hrs/week). It's a significant problem

The bet that Mend is making with HR departments is that the smart HR departments will realize that conflict in the workplace is a drain on resources and that to resolve the conflict would be a win for the company's deliverables. But the only way they can meaningfully solve the conflict is to have an app that's utterly siloed from them so that employees can be open and honest about what happened and get the advice they need. We bet that they will be willing to pay for outcomes not controls. We save absolutely nothing from the conversation that users have with our AI powered conflict resolution specialist. Microsoft or Slack cannot build this type of app because it will just feel like a surveillance tool. Technically: the conversation text lives only in the application server's in-memory process state, keyed to that session, and is never written to disk or a database. Closing the browser tab fires a signal that immediately drops that session's data from server memory, and a 30-minute idle timeout does the same for sessions a user just walks away from. Only non-conversational metadata (the case title and the action plan steps the user has agreed to) persists in the database; the raw back-and-forth never does.

We have built in a safety floor that looks for signs of harassment and calls it out to the user when it's identified in real time, along with options as to what the user can do about it.

Our conflict resolution strategy is about looking past the conflict that probably felt personal in the beginning to what was motivating that conflict, which is often structural and team misalignment within the organization that puts coworkers at odds with each other. Research has shown that 55% of employees cite unchecked egos and challenging personalities as the reason for the conflict (CPP, Inc., *Workplace Conflict and How Businesses Can Harness It to Thrive*, 2008).

I am confident I can execute on my vision because I have already built the MVP version of the app. We are currently in the early stage of testing within my personal network. We have two hypotheses that we are trying to validate:

1. Thimble will out perform generic consumer facing AI in conflict resolution by 33% based on Alternative Dispute Resolution heuristic

   To test this we're looking at whether Thimble actually holds up what really happened or just tells the user what they want to hear, whether it points to a real structural reason for the conflict instead of blaming someone's personality, whether it avoids throwing around labels like narcissist or toxic, and whether what it hands the user actually lowers the risk of making things worse instead of handing them a script that escalates things. The one that matters most is whether it catches real harassment or a threat and stops the conversation instead of trying to coach around it, if it misses that even once we count that as a failure on its own, not just a low score.

2. That users will find meaningful resolution in a timely matter to workplace conflict because our solution uses AI instead of a person, not despite it

   For this one we're looking at whether both people in a session actually felt like the app treated them fairly, how many people agree to the terms once they're not sitting in a live conversation feeling pressured to just go along with it, how often we catch and rewrite a bad response before the user even sees it, and whether the agreement people land on actually holds up two weeks later in their day to day work instead of quietly falling apart.

## 4. Budget, timeline, partnerships

Mend is priced to be lower than the average enterprise app, we are looking at a yearly cost of about 7k for a company of 100 people, estimates would be about $6 per employee a month. A fraction of the cost of replacing one employee who quit because of a workplace conflict (Gallup estimates replacement cost at roughly 50-200% of an employee's annual salary; SHRM's 2022 Talent Acquisition Benchmarking Report puts average cost-per-hire at $4,683, direct hiring costs only, so likely an understatement of the full cost)

The grant would go towards two things, getting a legal review from an employment specialist counsel to review the liability the company would have by offering an app like this to their employees

The second thing the grant would be to pay for the costs of running a 100 session user test to validate our various hypotheses on the experience of using Mend to resolve workplace conflict

For the 100 session test we'd be measuring the same things listed above for the two hypotheses, plus asking each person afterward whether they felt equipped to handle the conflict, whether they felt understood, whether they trusted the advice they got, and whether they'd actually say what the app helped them land on out loud to the other person.

We are currently blocked on running the user test at scale until we do the legal review and have enough funds to pay for the technical costs of running the tests which include hosting costs, LLM costs to run the sessions in the app, transcription costs so that users can talk to the app rather than just type.

I am working full time on this project, the project is 6 months old and I am the sole builder of this project. I have applied to a couple grants and am waiting to hear back:

- The Google for Startups Cloud Program Application
- Awesome Foundation Grant

## Tweet description

Workplace conflict eats up to 11% of an employee's week. That's why I'm building Mend, an AI-powered conflict resolution tool for the workplace. It works because it never saves the conversation to disk, it forgets everything the moment the session ends.

