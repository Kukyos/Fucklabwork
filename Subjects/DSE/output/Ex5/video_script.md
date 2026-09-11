# Ex 5 — Code explanation (teaching cues)
*Regression analysis · India rental house price · URK24CS1021*

> Mam wants this to sound like **you teaching a junior**, not you reading the code.
> Order is always: **the question first, why this technique and not another, then the code.**
> Glance at these cues, look at the output on screen, say it in your own words. ~7 min.

**Open with** — who you are, reg no URK24CS1021, Experiment 5.
Then the hook, in your own words: *"Every experiment so far has been about describing data
that already exists. This one is the first time I ask the data a question it doesn't
literally contain: given a house I've never seen, what should it rent for per square foot?
That's regression — fit a function to what you know, then use it on what you don't."*

---

**The dataset, and a problem in it (Q1–Q9)**
- Say what the data is: 13,910 rental listings from Delhi, Mumbai and Pune. The Kaggle
  download ships one CSV per city with the same columns, so I concatenated them — and that
  turns `city` from a useless constant into a real three-level predictor.
- Then the honest bit, and do **not** skip it: my assigned target is **Price per Square
  Foot**. The dataset has a `priceSqFt` column. **It is empty in all 13,910 rows.**
  Show the `notna().sum()` printing 0. So the target had to be derived: rent ÷ built-up area.
- Why that's fine: price per square foot is *defined* as that ratio. I'm not inventing a
  target, I'm computing the one the column was supposed to hold.
- `house_size` is text — `"1,020 sq ft"`. Point at the strip-and-convert line. Real-world
  data is like this; half of any data science job is this line.

**The one decision that matters — what NOT to feed the model (Q10)**
- This is the concept worth the most time. Ask it out loud: *why isn't `price` a feature?*
- Answer: because the target **is** `price / size`, and `size` is already a feature. Give
  the model `price` and it just divides two of its inputs and scores a perfect R². That's
  **data leakage** — the model looks brilliant in the notebook and is worthless on a house
  that hasn't been priced yet, which is the only kind you'd ever use it on.
- Rule to leave them with: *if a feature wouldn't exist at the moment you need the
  prediction, it can't be a feature.*
- Then `location`: 702 distinct localities. One-hot encoding all of them makes a matrix
  wider than it is tall. Keep the top 30 by frequency, bucket the rest as "Other". Say the
  cost of that out loud — you're deliberately throwing away micro-location detail, and
  you'll see it again in the leftover error at the end.

**Simple vs multiple (Q11–Q12)**
- Simple linear first, size only: R² ≈ 0.16. Say what that number *means* — size explains
  about a sixth of why one flat costs more per square foot than another. Five-sixths is
  something else.
- Then multiple: R² ≈ 0.38, more than double. Point at the top coefficients — they're
  city and locality dummies. **That's the finding:** rent per square foot is a question of
  *where*, not *how big*. Bigger houses aren't more expensive per foot; posh areas are.
- Explain R² once, properly: the share of the variation the model explains. 1.0 is perfect,
  0 is no better than always guessing the average. And RMSE: the typical error, **in the
  units of the target** — rupees per square foot — which is why you quote it alongside R².

**Polynomial, Lasso, Ridge (Q13–Q15)**
- Polynomial degree 2: every squared term and every pairwise interaction, so the fit can
  bend. It expands 39 features into over 800 — and gains essentially nothing. Say what
  that tells you: **the relationship was already about as linear as it's going to get.**
  A technique that doesn't help is still a result.
- Lasso and Ridge: same linear fit, plus a penalty on how big the coefficients get. The
  difference in one line — **Ridge shrinks coefficients, Lasso can shrink them to exactly
  zero**, so Lasso doubles as feature selection.
- Why scale first: the penalty is on coefficient *size*, and `size_sqft` runs into the
  thousands while a dummy column is 0 or 1. Without `StandardScaler` the penalty punishes
  whichever column happens to use big numbers. That's what the `make_pipeline` is for.
- Both score the same as plain multiple regression. Say why, don't apologise for it:
  penalties fix **overfitting**, and with 11,000 training rows against 39 features there
  is no overfitting to fix. Regularisation earns its keep when features approach or exceed
  rows — not here.

**The table and what it's really saying (Q16–Q18)**
- Stress that the table is built from a `results` list the models appended to as they ran —
  nothing in it was typed by hand. If you re-run, the table re-computes.
- Predicted-vs-actual plot: the red line is where a perfect model would put every point.
  Ours spreads around it and clearly under-predicts the very expensive listings. Say what
  that means — the model has no feature that captures "this is a premium address".
- Close on the honest reading: **R² ≈ 0.38 is not a failure, it's the ceiling of the
  features I kept.** The error that's left is mostly the 672 localities I collapsed into
  "Other". If I wanted a better number I'd go back to the features, not to a fancier model —
  and that's the real lesson: model choice moved the score by less than 0.01, feature
  choice moved it by 0.22.
