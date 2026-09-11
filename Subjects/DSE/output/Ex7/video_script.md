# Ex 7 — Code explanation (teaching cues)
*Clustering · human cognitive performance · URK24CS1021*

> Mam wants this to sound like **you teaching a junior**, not you reading the code.
> Order is always: **the question first, why this technique and not another, then the code.**
> Glance at these cues, look at the output on screen, say it in your own words. ~7 min.

**Open with** — who you are, reg no URK24CS1021, Experiment 7.
Then the hook: *"Experiments 5 and 6 both had an answer column — a price, a genre — and the
model's job was to reproduce it. This dataset has no answer column at all. 80,000 people,
their sleep, stress, caffeine, screen time, reaction time and test scores, and nobody has
labelled any of them. The question changes completely: not 'what is this person?' but
**'do these people fall into natural groups at all?'** And the honest answer here turns out
to be 'sort of, on three of the eight columns' — which is a more interesting finding than
a clean win."*

---

**Three decisions before any algorithm runs (Q9)**
- **`User_ID` goes.** It's a unique key. Distance between U1 and U2 is meaningless.
- **`AI_Predicted_Score` goes**, and this is the one worth explaining. It is a model's
  *prediction of* `Cognitive_Score` — the two correlate at about 0.99. Keeping both is
  feeding the same information in twice, and since clustering is nothing but distance, a
  duplicated column silently gets double the vote.
- **Sampling: 2,000 rows, not 80,000.** Say why precisely — agglomerative and spectral
  clustering both need an n×n matrix of every pair of points. At 80,000 rows that's 6.4
  billion numbers, roughly 51 GB. This isn't "it would be slow", it's "it would not run".
  All three algorithms get the *same* sample so the comparison is fair.
- **Scaling is not optional here.** Caffeine intake runs 0–500, sleep duration 4–9. Without
  `StandardScaler`, "distance between two people" means "difference in caffeine" and nothing
  else. Every column gets mean 0 and std 1 so each one gets an equal vote.

**Choosing k with nothing to check against (Q10)**
- Frame the problem: in supervised learning you tune against a test score. Here there is no
  score. So k has to be *argued* for.
- **Elbow:** inertia is the total spread inside the clusters. It always falls as k rises —
  at k = n it's zero and every point is its own cluster. You're looking for the bend where
  extra clusters stop buying much.
- **Silhouette:** for each point, how much closer it sits to its own cluster than to the
  next nearest, from −1 to +1. Averaged over everything.
- Now read the actual numbers out and be straight about them: **the elbow is gentle and the
  best silhouette is about 0.16.** Both are telling you the same thing — these are soft
  regions in one cloud, not separate islands. I went with k = 3 because the three groups
  come out interpretable, and I'll show that at the end rather than assert it.

**The three algorithms — one line each on how they think (Q11–Q13)**
- **K-means:** drop 3 centres, assign everyone to the nearest, move each centre to the
  average of what it caught, repeat. Fast, but it assumes clusters are roughly round blobs
  of similar size, and you have to tell it k in advance.
- **Agglomerative:** bottom-up. Start with 2,000 clusters of one person each, repeatedly
  merge the two closest, stop at 3. The key property: **merges are permanent.** It never
  reconsiders, so an early bad merge is carried all the way.
- **Spectral:** builds a graph of who is near whom, then cuts the graph where the
  connections are thinnest. This is the one that can find crescents and rings — shapes
  k-means fundamentally cannot, because k-means can only draw straight boundaries between
  centres.

**Displaying the clusters (Q14)**
- Say what PCA is doing and, more importantly, what it is *not* doing: it did not cluster
  anything. The clustering happened in all 8 dimensions. PCA only compresses those 8 down
  to the 2 directions with the most variation so the result can be drawn on a page.
- Read out how much variation those two components keep — it's well under half. So say the
  caveat: **things that look overlapping in this picture may be cleanly separated in a
  dimension the plot doesn't show.** The picture is a shadow, not the object.

**The table, and the honest reading (Q15–Q17)**
- Three metrics, and say which way each one points: silhouette higher is better,
  Calinski-Harabasz higher is better, Davies-Bouldin **lower** is better.
- K-means wins all three. Don't just celebrate — explain the catch: silhouette and
  Calinski-Harabasz both reward **compact, round clusters**, and compact round clusters are
  precisely what k-means is built to produce. Scoring k-means with them is a little like
  letting it mark its own homework. Worth saying out loud; it's the kind of point that gets
  a follow-up question.
- Agglomerative comes last — tie it back to the permanent-merge property you already
  explained.
- **Then the payoff, Q16.** Group the original columns by cluster and look at the averages.
  Measure the gaps **in standard deviations**, not raw units — otherwise caffeine (0–500)
  looks important next to sleep (4–9) purely because its numbers are bigger. Done properly,
  the centres differ by about 1.7–1.9 deviations on **Cognitive_Score, Stress_Level and
  Reaction_Time**, and by less than a third of a deviation on age, sleep, screen time and
  caffeine.
- Land it: *the clusters are real — one group is fast and high-scoring, one is slow and
  stressed, one is slow and unstressed. They just aren't well separated in all eight
  dimensions, because five of those eight are noise as far as the grouping is concerned,
  and the silhouette averages over all eight.* A low silhouette meant "weak separation", not "meaningless clusters" —
  and knowing the difference is the whole point of looking at the profile table instead of
  stopping at the score.
