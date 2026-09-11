# Ex 6 — Code explanation (teaching cues)
*Classification · music genre dataset · URK24CS1021*

> Mam wants this to sound like **you teaching a junior**, not you reading the code.
> Order is always: **the question first, why this technique and not another, then the code.**
> Glance at these cues, look at the output on screen, say it in your own words. ~7-8 min.

**Open with** — who you are, reg no URK24CS1021, Experiment 6.
Then the hook: *"Last experiment I predicted a number. This one predicts a label: given
only the audio measurements of a track — how danceable, how loud, how fast — which of
eleven genres is it? And the interesting part isn't which model wins. It's that two of
these five models fail in **opposite** directions, and that's the whole lesson."*

---

**Set the bar before you fit anything (Q1–Q8)**
- 17,996 tracks, 11 genre classes, and they're badly imbalanced — the biggest class is
  about 28% of the data.
- Do this *before* any model: **what does guessing get you?** Always shout the biggest
  class and you're right ~28% of the time. Say it plainly — *any accuracy below that is
  worse than not thinking.* Accuracy on its own is a liar on imbalanced data; that's why
  the classification report gives precision and recall per class.

**Two real defects in the file (Q9–Q10)**
- Point at the column name: `duration_in min/ms`. The name is a confession. ~2,580 rows are
  in minutes, ~15,400 in milliseconds, in the same column. A model given that column would
  think some three-minute songs last 0.00005 of whatever the others last.
- The fix is one `np.where` — anything under 100 is already minutes, everything else gets
  divided by 60,000. Say how you *found* it: `describe()` showed a min of 0.5 and a max of
  1.4 million. Two orders of magnitude apart in one column is always a units bug.
- Then the nulls: Popularity 428, key 2,014, instrumentalness 4,377. Median, not mean —
  the median doesn't move when a few extreme values sit in the tail. Mention the honest
  caveat: imputing 4,377 values is a real intervention, and that column is now partly
  invented.

**One decision that keeps the comparison fair (Q11)**
- Artist and track name go out. Nearly every row has a unique one, so they're an identifier,
  not a pattern — a model that learns them has memorised a lookup table.
- Then the sampling, and be upfront about why: **SVM training is quadratic in the number of
  rows.** On 18,000 rows it crawls. So all five models run on the *same* 5,000-row sample.
  The point is that changing the sample for one model would make the comparative table
  meaningless. Same rows, same split, same scoring.
- `stratify=y` — with 11 unbalanced classes a random split could hand a rare class almost
  entirely to the test set. Stratify keeps the proportions identical on both sides.

**The five models — one line each on *why they're different* (Q12–Q16)**
- **KNN:** no training at all, it just remembers the points and takes a vote of the five
  nearest. Needs scaling: tempo sits near 120, danceability between 0 and 1, so without a
  scaler "distance" means "difference in tempo" and nothing else.
- **Decision tree:** asks yes/no questions on one feature at a time. Scaling is irrelevant
  to it — a threshold is a threshold. `max_depth=10` is a leash; an unlimited tree grows
  until every leaf holds one song, which is memorising.
- **Random forest:** 200 trees, each on a random slice of rows and features, then they vote.
  The idea worth saying: individual trees are unstable, but their *mistakes* are
  uncorrelated, so averaging them cancels the noise out.
- **Logistic regression:** one straight boundary per class. The simplest thing here.
- **SVM with an rbf kernel:** looks for the boundary with the widest margin, and the kernel
  lets that boundary curve.

**The part that matters — overfitting vs underfitting (Q17–Q18)**
- Put the train and test columns side by side and read them out.
- **Random Forest: ~0.98 on training, ~0.49 on test.** That is the textbook picture of
  **overfitting**. Say what it actually means: the forest has learned the training songs,
  not the genres. The train score isn't a result, it's a warning.
- **Logistic Regression: ~0.45 training, ~0.46 test.** It does no better on data it has
  already *seen* than on data it hasn't. That's **underfitting** — the model isn't complex
  enough to capture the pattern, so it does equally badly everywhere. Note the tell: an
  underfit model's train and test scores are both low and almost equal.
- The line to leave them with: **you diagnose from the gap, not from the height.** A big
  gap means overfitting, no gap and low scores means underfitting, small gap and decent
  scores is what you actually want.
- Confusion matrices: point at the bright column belonging to the biggest class. The model
  quietly learns that guessing the common genre is a good bet, so small classes get absorbed.
  That's imbalance showing up as a *shape* in the matrix, which is why you look at the matrix
  and not just the accuracy.
- Close honestly: ~49% on 11 classes is far from great, but it's roughly double the guessing
  baseline, so the audio features genuinely carry genre information — just not enough of it
  to separate eleven overlapping genres cleanly.
