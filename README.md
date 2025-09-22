# InboxPilot

InboxPilot is an AI-powered command-line tool that turns incoming emails into actionable replies. Instead of copying and pasting text between Gmail and a chatbot, InboxPilot provides a streamlined workflow: paste the email, specify how you want to respond, and generate a polished draft. You can then either save it directly as a Gmail Draft or send it immediately.

## Features
* Paste any incoming email and type how you want to respond (e.g., accept invitation, politely decline, request more details)
* AI drafts a reply that follows a professional tone and your intent
* Choose to save the reply as a Gmail Draft or send it instantly
* Runs on local LLMs with Ollama for privacy and speed
* Integrates directly with Gmail through the Gmail API (OAuth)

## Tech Stack
* Python
* Gmail API with OAuth (google-api-python-client, google-auth-oauthlib, google-auth-httplib2)
* Ollama with llama3.1 (or other local LLMs)
* Requests library for local inference calls

## How to Run

### Prerequisites
* Python 3.9+
* Gmail account with API access enabled
* Google Cloud project with Gmail API enabled
* OAuth 2.0 client credentials (downloaded as `credentials.json`)
* Ollama installed locally

### Setup
1. Clone this repository

   git clone https://github.com/<your-username>/InboxPilot.git
   cd InboxPilot
   
2. Create a Python virtual environment

   python3 -m venv .venv
   source .venv/bin/activate
   
3. Install Dependencies
   pip install --upgrade pip
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib requests

4. Place your credentials.json (Google OAuth client secret) in the project root
5. Install & run Ollama
   brew install ollama
   ollama serve
   ollama pull llama3.1

### Running InboxPilot
1. In one terminal, Start Ollama:
   Ollama serve
2. In another terminal, run the script:
   python inboxpilot.py
3.	Paste the full email you received, then type END on its own line
4.	Enter your instructions (e.g., “accept politely and ask for details about timeline”)
5.	Review the AI draft
6.	Choose draft to save to Gmail drafts or send to send immediately

## Future Roadmap

InboxPilot was built during a hackathon with a focus on productivity. Planned enhancements include:
	•	Preset response types (accept, decline, request info) for even faster replies
	•	Style guide and signature customization for individuals and organizations
	•	Lightweight team features such as shared tone profiles and style consistency
	•	Optional GUI to make the tool more accessible beyond the command line
	•	Support for additional providers beyond Gmail

## Track Alignment:
InboxPilot aligns with two hackathon tracks:

**Business Productivity**
Helps professionals streamline daily workflows, reducing time spent on repetitive email tasks and improving response consistency.

**Productivity for Young Professionals**
Supports early-career individuals in managing communication efficiently, saving up to an hour each day and freeing time for higher-value work.

