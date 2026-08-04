# Ex 2 — Code explanation (talking cues)
*Pandas on fanspeed.csv · URK24CS1021*

> Cue cards, ~5 min. **Glance, don't read** — look at the cell on screen and say it in your own words. Keep it relaxed, like you're showing a friend.

**Open with:** who you are + reg no URK24CS1021, Experiment 2, Pandas, scenario = exploring a fan speed dataset (temperature vs observed fan speed).

**Cell 1** — import pandas, load fanspeed.csv into a DataFrame
**Cell 2** — head(10) -> first ten rows
**Cell 3** — tail(8) -> last eight rows
**Cell 4** — shape, columns, dtypes -> quick shape check
**Cell 5** — describe() -> mean/std/min/max/quartiles
**Cell 6** — plant a few nulls on purpose; isnull().sum() to find them
**Cell 7** — fillna with the column mean; confirm nulls are gone
**Cell 8** — loc by label -> rows 5-8, Temperature column
**Cell 9** — boolean condition in brackets -> conditional slicing
**Cell 10** — arithmetic column; apply + lambda -> High/Low label column
**Cell 11** — sort_values descending -> fastest readings on top
**Cell 12** — groupby Speed_Level, mean per group
**Cell 13** — rank with dense method; sort by it to sanity check

**Close with:** loaded and inspected the data, found and imputed nulls, sliced it different ways, derived new columns, sorted/grouped/pivoted it, and ranked it — the standard pandas exploration toolkit.