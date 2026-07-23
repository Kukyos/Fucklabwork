# Ex 1 — Code Explanation (video script)
*Manufacturing Quality Control · URK24CS1021 — aim ~5 minutes, spoken casually.*

**Intro**
Hi, I'm [name], register number URK24CS1021. This is Experiment 1 of the Data Science Ecosystem Lab, working with NumPy and Pandas. My scenario is Manufacturing Quality Control — I'm analysing the hourly defect rates from a factory over a 24-hour production day. Let me walk through my notebook cell by cell.

**Cell 1**
First I import numpy and set a seed, so the random numbers come out the same every time I run it. Then I make an array of 24 defect rates — one for each hour of the day — somewhere between 0.1 and 5 percent, and round them to two decimals so it's easy to read.

**Cell 2**
Here I just index into the array with square brackets to pull out the defect rate at hour 12.

**Cell 3**
The night shift runs from 8 in the evening to 6 in the morning, which wraps around midnight. So I slice the last few hours of the day and the first few hours of the next, and concatenate them into one array.

**Cell 4**
Next I reshape the 24 hours into a 3 by 8 grid — three shifts of eight hours each — so I can analyse it shift by shift instead of one long line.

**Cell 5**
Then I loop through every hour with enumerate, and print out only the ones where the defect rate went above 3 percent — those are my problem hours that need attention.

**Cell 6**
Here I make a second array of temperatures and stack it on top of the defects with vstack, so now each hour has both its defect rate and its temperature in one 2 by 24 array.

**Cell 7**
After that I split the day into three equal shifts and print each one out on its own line.

**Cell 8**
Using a boolean mask, I keep only the critical defects — the hours where the rate went above 4 percent.

**Cell 9**
This one line sorts all the defect rates in ascending order, smallest to largest.

**Cell 10**
And here I filter for the hours in the acceptable range — between 0.5 and 1.5 percent — by combining two conditions with an and.

**Cell 11**
Now switching to pandas. I take a plain list of product names and turn it into a Series, which just gives each product a little index next to it.

**Cell 12**
And finally I build a DataFrame from a dictionary, so the products and their tolerance values line up neatly in a table with rows and columns.

**Outro**
So that's the whole notebook — I started with raw hourly defect data and used NumPy to index, slice, reshape, filter and sort it, then used Pandas to organise product information into a Series and a DataFrame. Everything ran and the output was verified. Thanks for watching.