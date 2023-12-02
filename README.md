# Automation
The goal of the files stored here is to 
1. Track and update the projects i work on in my own time for fun and automation projects
2. Potentially help someone who is beginning their Python journey understand what is going on
3. Hopefully show some people who don't understand the power in the simplicity of Python in terms of it's practical usage.

IT IS NOT
1. Python best practices
2. Examples of how good a developer i am - because GPT is helping me alot...

**POJECT 1
Email Categorisation (template)**
Goal: My personal email is a mess - rather than unsubscribe to all of the junk i have going through it since highschool - I figured GPT could help me with it.
I namely just wanted to make sure i didn't miss Bills and receipts going through my email because of the junk.
I also didn't want to use GPT online because i didn't want my personal data being fed to the Open AI feed online. 

Outcome:
After a week or so i have a script that windows task scheduler can run to clean up my emails. 

Review:
The local model is a little slow and the limited text that it can intake meant i couldn't use the body of the email like i initially planned to.
For what it is needed for it actually works great, may in future have to run a secondary call to the LLM to reclassify the classifications because sometimes they come out funky - e.g. [support] came out as a category, which i would then have to feed back into the LLM.


