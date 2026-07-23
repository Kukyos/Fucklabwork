# Ex 1 — Code explanation (talking cues)
*Manufacturing Quality Control · URK24CS1021*

> Cue cards, ~5 min. **Glance, don't read** — look at the cell on screen and say it in your own words. Keep it relaxed, like you're showing a friend.

**Open with:** who you are + reg no URK24CS1021, Experiment 1, NumPy & Pandas, scenario = analysing a factory's hourly defect rates over 24 hours.

**Cell 1** — import numpy, set a seed so the random numbers repeat; make 24 hourly defect rates, 0.1-5%, rounded
**Cell 2** — just index in; pull out hour 12's rate
**Cell 3** — night shift wraps past midnight; so slice the end + the start and join them
**Cell 4** — reshape 24 hours into 3x8; = three shifts of 8 hours
**Cell 5** — loop through the hours; print the ones over 3% -> problem hours
**Cell 6** — second array of temperatures; stack it on the defects -> 2x24
**Cell 7** — split the day into 3 equal shifts; print each
**Cell 8** — boolean mask for anything over 4%; = the critical hours
**Cell 9** — one line to sort ascending
**Cell 10** — filter the acceptable band, 0.5-1.5%; two conditions with an &
**Cell 11** — pandas now: a plain list -> Series; it adds an index
**Cell 12** — a dict -> DataFrame; lines up product + tolerance as a table

**Close with:** NumPy handled indexing/slicing/reshaping/filtering/sorting, Pandas made the Series + DataFrame; it all ran and the output checked out.