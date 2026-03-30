# PourFaireQuoi (pqf)

PourFaireQuoi is yet another todo list app, but as more task managers focus on \*what\* and \*when\*, this app focus on "How" and "Why", “but” “or”, ...etc.  It will allow to build a reasoning Engine for complex projects, tracking reasoning, choice and history.

The idea is to build a minimal, simple app for prototyping and demo.
The app name is pourfairequoi, abbreviated to “pfq”.


### Goal of the app


- tool to brainstorm ideas
- planify projects
- brain dump/mindmapping
- identify real motivation and alternative routes
- keep a log
- identify project roadblock
  - Why it is stuck ?
  - break down to smaller steps
  

It is more a personal tool, than a profesional/entreprise task manager.
Thus the features:
- local file for privacy
- simplicity: terminal based

Could eventually be paired with IA but:
- should work without IA
- local IA (ollama)

## Architecture
- Each task (or project) is a yaml file
- All data is stored in these files

Example of file "m11ab_vintage_radio_build.yaml":
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
    - "get elec gears: soldering iron, voltemeter"
    - (opt) find a fablab
    - buy a first old radio #buy_old_radio
    - build the new electronics #radio_elec
but:
    - budget <300euros #budget300
    - "don't to stop midcourse"
    - lost time and money
or:
    - Start a less complex build (alarm clock)
```

Each line could point to another file. The link is defined is hastag//comment + task_id (TBD)


The UI is terminal based (unix) with a vertical split screen:

on the left part of the screen:
- parsed view of the doc
- select a line
- edit the line in the bottom

Single line edit with key words:
OR ... why/to ... how/by ...



On the right part of the screen :
- the linked doc is shown
- if no link, search tool to add a link
- focus on this node if it exists (then it will move to left part)

## Tech
Build using python with:
- Click
- Rich and Textual

## Open questions
- naming files convention and id creation
- flatten the dir structure for simplicity ?

