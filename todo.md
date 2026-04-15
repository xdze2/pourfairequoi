# Next actions


2. **Fix: back / history navigation** — `b` key works but there is no visual indication; add a breadcrumb line in the header, or at least make `Esc` in the subgraph go back



2. **Feature: search in home page** — `/` to filter the home list by description, same pattern as `LinkPickerPane`




- key binding:
    - always active: "q", "h", "b", "Tab": not working
    - ...


- Root node vs home page --> same context, same ui
make the home page similar to graph view


- add tags ? no yet


- Better color palette

- make node view fct of type

goal: ****
project: timeline
milestone: timeline ?
task:  ?
question: ? answer
spec: ...
constraint: ...
event: x DATE

- Show duplicate node in tree, but do not expand (^)



--- 

- derive status from the graph, dates


Staleness signal — nodes with active status and start_date older than their horizon. "This has been 'active' for 3 months on a 'week' horizon — is it stuck?"
Missing fields highlight — show nodes lacking status, type, or any how children as "incomplete". Makes the gap visible without nagging.


"What is actually blocking me?" — trace from a root goal down to the first stuck leaf. Show the path. This is the one thing that's genuinely hard to see on paper with 60 nodes.