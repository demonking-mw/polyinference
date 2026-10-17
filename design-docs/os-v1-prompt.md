Note: design-docs/simplified-os/polyinference-os-review.json contains my responses to the quesitons listed in the html audit doc.

The docs in polyinference contains much info on the project. The agent is also built already (and being tested right now) Your task is to build the first (simple) os. the most useful docs snould be in design-docs/simplified-os. Every other docs in the project, however, contains useful information for your effort. You are to plan carefully, develop the os, and test it thoroughly. A few notes:
1. you must integrate the cloud endpoint to use llm api and codex agents. See codex agent proxy brief.md for more info
- you are to make a new branch and work on there. There will be testing efforts happening on the main branch for the agent, merging won't happen till much later, so your new branch will be the source of work for the OS.
2. You are to replace the placeholder OS for testing. Implement all the designed features unless it's clear that the feature is for a future iteration.
3. You must pay close attention to every other docs as well. They contain critical information and must be considered
4. I included the answers from the audit html, that would be very important for your system design
5. one example case of concern: when 4 runs together and one fail, the desired behavior is: make the commit without merging, exit critical section, let all processes currently running to finish (and merge the commit), then enters sprint management to deal with this and replan sprint.