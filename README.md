# PourFaireQuoi (pfq)

PourFaireQuoi is yet another todo list app, but while most task managers focus on *what* and *when*, this app focuses on *how*, *why*, *but*, *or*, and other reasoning dimensions. It allows you to build a reasoning engine for complex projects, tracking decisions, alternatives, and history.

The goal is a minimal, simple app for prototyping and personal use.
The app name is pourfairequoi, abbreviated to "pfq".


## Goals

- Brainstorm ideas
- Plan projects
- Brain dump / mind mapping
- Identify real motivations and alternative routes
- Keep a decision log
- Identify project blockers
  - Why is it stuck?
  - Break it down into smaller steps

It is more a personal tool than a professional/enterprise task manager.
Key design principles:
- Local files for privacy
- Simplicity: terminal-based

Could eventually be paired with AI, but:
- Should work without AI
- Prefer local AI (e.g. Ollama)

## Architecture
- Each task (or project) is a YAML file
- All data is stored in these files

Example file `m11ab_vintage_radio_build.yaml`:
```yaml
description: Build a vintage radio
start_date: ...
status: stuck
why:
    - fun
    - learn stuff
    - get a nice radio object
    - have a project to show #a1y89
need:
    - time
how:
    - "get elec gear: soldering iron, voltmeter"
    - (opt) find a fablab
    - buy a first old radio #buy_old_radio
    - build the new electronics #radio_elec
but:
    - budget <300 euros #budget300
    - risk stopping midcourse
    - lost time and money
or:
    - Start a less complex build (alarm clock)
```

Each line can point to another file. Links are defined by a hashtag comment + task ID (TBD).


## UI

Terminal-based (Unix) with a vertical split screen:

**Left panel:**
- Parsed view of the document
- Select a line
- Edit the line at the bottom

Single-line edit with keywords:
`OR ... why/to ... how/by ...`

**Right panel:**
- The linked document is shown
- If no link exists, a search tool allows adding one
- Focus moves to this node (then shifts to the left panel)

## Tech
Built with Python:
- Click
- Rich and Textual

## Open questions
- File naming convention and ID creation
- Flatten the directory structure for simplicity?
- Interaction for the edit line
- How to insert new line, delete a line
