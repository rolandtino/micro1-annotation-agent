# Micro1 Annotation Agent

A tool calling AI agent built from scratch in Python, no framework, no template. Tracks Micro1 for open roles matching my skills and sends an email alert when it finds one. Built to learn how agentic AI actually works under the hood before touching tools like LangChain or CrewAI.

## What it does

- Holds a real back and forth conversation in the terminal
- Decides on its own when it needs to search the web instead of answering from memory
- Remembers past conversations even after the program is closed and reopened, using a local memory file
- Checks Micro1 specifically for open roles, compares results against a personal skill list, and flags a clear alert when something matches
- Tracks changes between checks, so it knows what's new versus what it already saw
- Sends an email alert automatically via Gmail when a skill match is found

## Why I built it

I work in AI data annotation and evaluation, and wanted to understand agentic AI by actually building one instead of reading about it. This started as a basic search agent and grew into something I use to track real opportunities on a platform I actively work with.

## Tech used

- Python
- Groq API (free tier, Llama 3.1 8B Instant model)
- DuckDuckGo search (via the `ddgs` package)
- Gmail SMTP for email alerts
- Local JSON files for persistent memory and change tracking

## How it works

The core loop:
1. User sends a message
2. The model decides if it needs a tool or can answer directly
3. If it needs a tool, it calls one (general web search, or the Micro1 check), gets the result back
4. If the Micro1 check finds a skill match, it sends an email alert automatically
5. The model checks the result and decides whether to answer or search again
6. Once it has enough, it gives a final answer and saves the full conversation to memory

## Setup

1. Install dependencies:
```
pip install groq ddgs
```

2. Get a free Groq API key at console.groq.com

3. Set it as an environment variable:
```
setx GROQ_API_KEY "your-key-here"
```

4. (Optional, for email alerts) Turn on 2-Step Verification on your Google account, then create an app password at myaccount.google.com/apppasswords. Set these as environment variables:
```
setx GMAIL_ADDRESS "youremail@gmail.com"
setx GMAIL_APP_PASSWORD "your-16-character-app-password"
```

5. Close and reopen your terminal so the new environment variables load, then run:
```
python agent.py
```

## What I learned

Building this taught me the actual mechanics behind "agentic AI": a model doesn't magically decide to act, it's a loop where you check its response, run whatever tool it asked for, and hand the result back until it's ready to answer. Every framework abstracts this same loop. Building it by hand made it click in a way reading docs never did.

## Build log

- v1: basic agent that could hold a conversation and decide when to call a web search tool
- v2: added persistent memory, conversation history saved to a local JSON file so the agent remembers past sessions even after closing the terminal
- v3: added a second tool for researching a specific platform, with basic keyword matching against a personal skill list
- v4: focused the research on Micro1 specifically, added change tracking so the agent can tell what's new since the last check
- v5: added email alerts via Gmail SMTP, fires automatically when a skill match is found, credentials read from environment variables so nothing sensitive is in the code
- v6: widened the skill matching keywords after noticing exact phrase matching missed near matches like "Evaluator" for "AI model evaluation"

## What I'd improve next

- Currently the agent only checks Micro1 when I manually ask it to, next step is wiring it into Windows Task Scheduler so it checks automatically every few hours
- Skill matching is still basic keyword matching, could be made smarter using the model itself to judge relevance instead of exact word matches
- Memory is a flat JSON file right now, fine for now but would need a real database if this scales up

