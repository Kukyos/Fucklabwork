"""Build Cleo's DSE Ex-7 record (clustering on the human cognitive performance
dataset). Content only - the docx/notebook/screenshot machinery lives in
dse_record.py.

    python Subjects/DSE/build_dse_ex7.py
"""
from __future__ import annotations

from pathlib import Path

from dse_record import Exp, build

HERE = Path(__file__).parent
OUT = HERE / "output" / "Ex7"

TITLE = "CLUSTERING TECHNIQUES"
DATE = "11/09/2026"

AIM = ("To apply unsupervised clustering algorithms in Python to a real-world dataset that "
       "carries no labels, and to compare K-means, agglomerative and spectral clustering "
       "using internal validation measures and a two-dimensional view of the resulting "
       "clusters.")

DESC = (
    "Clustering is unsupervised: there is no target column, so the algorithm has to find "
    "groups in the data by itself. K-means picks k centres and repeatedly reassigns every "
    "point to its nearest centre until the centres stop moving. Agglomerative clustering "
    "works bottom-up, starting with every point as its own cluster and repeatedly merging "
    "the two closest ones. Spectral clustering builds a graph of which points are near "
    "which, and cuts that graph where the connections are weakest, which lets it find "
    "shapes K-means cannot. With no labels to check against, the result is judged by "
    "internal measures: the silhouette score (how much tighter a point sits with its own "
    "cluster than the next nearest, from \u22121 to +1), the Calinski-Harabasz index (higher "
    "is better) and the Davies-Bouldin index (lower is better)."
)

QUESTION = (
    "Dataset: Human Cognitive Performance Analysis\n"
    "(https://www.kaggle.com/datasets/samxsam/human-cognitive-performance-analysis)\n"
    "\u2022 Import the dataset.\n"
    "\u2022 Display the first 10 rows of the dataset.\n"
    "\u2022 Display the last 8 rows of the dataset.\n"
    "\u2022 Display information about the dataset: information, column names, shape, "
    "statistical inferences, data types.\n"
    "\u2022 Perform the following clustering and measure the performance: K-means "
    "clustering, Agglomerative Clustering, Spectral Clustering.\n"
    "\u2022 Display the clusters for all the techniques.\n"
    "\u2022 Draw a comparative table of performance metrics for all the techniques.\n"
    "\u2022 Document your interpretations."
)

PREAMBLE = (
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "from sklearn.preprocessing import StandardScaler\n"
    "from sklearn.decomposition import PCA\n"
    "from sklearn.cluster import (KMeans, AgglomerativeClustering,\n"
    "                             SpectralClustering)\n"
    "from sklearn.metrics import (silhouette_score, calinski_harabasz_score,\n"
    "                             davies_bouldin_score)\n\n"
    'sns.set_theme(style="whitegrid")\n'
    'plt.rcParams["figure.figsize"] = (7, 4.5)\n'
    'pd.set_option("display.width", 100)\n'
    'pd.set_option("display.max_columns", 20)\n'
    'pd.set_option("display.max_colwidth", 20)\n\n'
    "SEED = 1021  # my reg no, so every run samples and seeds the same way\n"
    "K = 3        # chosen in question 10, below\n"
    "results = []  # every algorithm appends its metrics here for the final table\n"
    "labels = {}   # and its cluster labels, for the comparison plot\n\n"
)

SECTIONS: list[tuple[str, str]] = [
    ("1. Import the dataset",
     'df = pd.read_csv("cognitive.csv")\n'
     'print("Rows loaded:", len(df))\n'
     'print(df[["User_ID", "Age", "Sleep_Duration", "Reaction_Time",\n'
     '          "Cognitive_Score"]].head())'),

    ("2. Display the first 10 rows of the dataset",
     'print(df.head(10))'),

    ("3. Display the last 8 rows of the dataset",
     'print(df.tail(8))'),

    ("4. Information about the dataset",
     'df.info()'),

    ("5. Column names",
     'print("Number of columns:", len(df.columns))\n'
     'for i, col in enumerate(df.columns, 1):\n'
     '    print(i, col)'),

    ("6. Shape of the dataset",
     'print("Shape (rows, columns):", df.shape)\n'
     'print("Rows   :", df.shape[0])\n'
     'print("Columns:", df.shape[1])\n'
     'print("\\nCounts for the three text columns:")\n'
     'for col in ["Gender", "Diet_Type", "Exercise_Frequency"]:\n'
     '    print(col, "->", df[col].value_counts().to_dict())'),

    ("7. Statistical inferences",
     'print(df.describe())\n'
     'print("\\nMissing values in the whole file:", df.isnull().sum().sum())'),

    ("8. Data types",
     'print(df.dtypes)\n'
     'print("\\nNumeric columns:", list(df.select_dtypes(include="number").columns))'),

    ("9. Choosing the features, sampling and scaling",
     '# User_ID is a unique key, not a measurement.\n'
     '# AI_Predicted_Score is a model\'s prediction OF Cognitive_Score - keeping it\n'
     '# would mean feeding the same information in twice and letting it dominate\n'
     '# every distance.\n'
     'drop = ["User_ID", "AI_Predicted_Score", "Gender", "Diet_Type", "Exercise_Frequency"]\n\n'
     '# agglomerative and spectral clustering both build an n x n matrix of\n'
     '# distances between every pair of rows. at 80,000 rows that is 6.4 billion\n'
     '# entries, so all three algorithms run on the same 2000-row sample.\n'
     'sample = df.sample(n=2000, random_state=SEED)\n'
     'num = sample.drop(columns=drop)\n'
     'print("Clustering on:", list(num.columns))\n'
     'print("Sample shape :", num.shape)\n\n'
     '# caffeine runs 0-500 and sleep 4-9, so without scaling "distance" would\n'
     '# mean "difference in caffeine" and nothing else\n'
     'X = StandardScaler().fit_transform(num)\n'
     'print("\\nBefore scaling (mean / std):")\n'
     'print(num.agg(["mean", "std"]).round(2))\n'
     'print("\\nAfter scaling, every column has mean 0 and std 1:",\n'
     '      np.allclose(X.mean(axis=0), 0), np.allclose(X.std(axis=0), 1))'),

    ("10. Choosing the number of clusters",
     '# there is no label to check against, so k has to be argued for.\n'
     '# elbow = where extra clusters stop reducing the within-cluster spread\n'
     'sweep = []\n'
     'for k in range(2, 9):\n'
     '    km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X)\n'
     '    sweep.append({"k": k, "inertia": km.inertia_,\n'
     '                  "silhouette": silhouette_score(X, km.labels_)})\n'
     'sweep = pd.DataFrame(sweep).set_index("k")\n'
     'print(sweep.round(4).to_string())\n'
     'print("\\nBest silhouette at k =", sweep["silhouette"].idxmax())\n\n'
     'fig, ax = plt.subplots(1, 2, figsize=(11, 4))\n'
     'sweep["inertia"].plot(ax=ax[0], marker="o", color="#4C72B0")\n'
     'ax[0].set_title("Elbow - within-cluster sum of squares")\n'
     'ax[0].set_xlabel("k")\n'
     'sweep["silhouette"].plot(ax=ax[1], marker="o", color="#C44E52")\n'
     'ax[1].set_title("Silhouette score")\n'
     'ax[1].set_xlabel("k")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("11. K-means clustering",
     '# k-means: place K centres, assign each point to the nearest, move the\n'
     '# centres to the mean of what they caught, repeat until nothing moves\n'
     'km = KMeans(n_clusters=K, random_state=SEED, n_init=10)\n'
     'labels["K-means"] = km.fit_predict(X)\n'
     'lab = labels["K-means"]\n\n'
     'print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())\n'
     'print("Iterations to converge:", km.n_iter_)\n'
     'print("Inertia:", round(km.inertia_, 2))\n'
     'print("\\nSilhouette       :", round(silhouette_score(X, lab), 4))\n'
     'print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))\n'
     'print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))\n'
     'results.append({"Technique": "K-means",\n'
     '                "Silhouette": silhouette_score(X, lab),\n'
     '                "Calinski-Harabasz": calinski_harabasz_score(X, lab),\n'
     '                "Davies-Bouldin": davies_bouldin_score(X, lab)})'),

    ("12. Agglomerative Clustering",
     '# bottom-up: start with 2000 clusters of one point each and keep merging\n'
     '# the two closest, using ward linkage, until only K are left\n'
     'agg = AgglomerativeClustering(n_clusters=K, linkage="ward")\n'
     'labels["Agglomerative"] = agg.fit_predict(X)\n'
     'lab = labels["Agglomerative"]\n\n'
     'print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())\n'
     'print("\\nSilhouette       :", round(silhouette_score(X, lab), 4))\n'
     'print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))\n'
     'print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))\n'
     'results.append({"Technique": "Agglomerative",\n'
     '                "Silhouette": silhouette_score(X, lab),\n'
     '                "Calinski-Harabasz": calinski_harabasz_score(X, lab),\n'
     '                "Davies-Bouldin": davies_bouldin_score(X, lab)})'),

    ("13. Spectral Clustering",
     '# builds a nearest-neighbour graph of the points and cuts it where the\n'
     '# connections are weakest, so it can follow shapes k-means cannot\n'
     'spec = SpectralClustering(n_clusters=K, random_state=SEED,\n'
     '                          affinity="nearest_neighbors", n_neighbors=10)\n'
     'labels["Spectral"] = spec.fit_predict(X)\n'
     'lab = labels["Spectral"]\n\n'
     'print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())\n'
     'print("\\nSilhouette       :", round(silhouette_score(X, lab), 4))\n'
     'print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))\n'
     'print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))\n'
     'results.append({"Technique": "Spectral",\n'
     '                "Silhouette": silhouette_score(X, lab),\n'
     '                "Calinski-Harabasz": calinski_harabasz_score(X, lab),\n'
     '                "Davies-Bouldin": davies_bouldin_score(X, lab)})'),

    ("14. Display the clusters for all three techniques",
     '# the data has 8 dimensions and a page has 2, so PCA compresses it down to\n'
     '# the two directions that carry the most variation, purely for drawing\n'
     'pcs = PCA(n_components=2, random_state=SEED).fit(X)\n'
     'XY = pcs.transform(X)\n'
     'print("Variation kept by the two components:",\n'
     '      pcs.explained_variance_ratio_.round(4),\n'
     '      "->", round(pcs.explained_variance_ratio_.sum(), 4))\n\n'
     'fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True, sharey=True)\n'
     'for ax, (name, lab) in zip(axes, labels.items()):\n'
     '    ax.scatter(XY[:, 0], XY[:, 1], c=lab, cmap="viridis", s=10, alpha=0.7)\n'
     '    ax.set_title(name)\n'
     '    ax.set_xlabel("PC 1")\n'
     'axes[0].set_ylabel("PC 2")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("15. Comparative table of performance metrics",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     'print(table.to_string())\n'
     'print("\\nHigher is better: Silhouette, Calinski-Harabasz")\n'
     'print("Lower is better : Davies-Bouldin")\n'
     'print("\\nBest silhouette        :", table["Silhouette"].idxmax())\n'
     'print("Best Calinski-Harabasz :", table["Calinski-Harabasz"].idxmax())\n'
     'print("Best Davies-Bouldin    :", table["Davies-Bouldin"].idxmin())\n\n'
     'fig, ax = plt.subplots(1, 3, figsize=(13, 4))\n'
     'for a, col, colour in zip(ax, table.columns, ["#4C72B0", "#55A868", "#C44E52"]):\n'
     '    table[col].plot(kind="bar", ax=a, color=colour, rot=20)\n'
     '    a.set_title(col)\n'
     '    a.set_xlabel("")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("16. What the clusters actually mean",
     '# a cluster number means nothing on its own - look at the averages inside it\n'
     'profile = num.assign(cluster=labels["K-means"]).groupby("cluster").mean().round(2)\n'
     'profile["members"] = pd.Series(labels["K-means"]).value_counts().sort_index()\n'
     'print(profile)\n\n'
     '# how far apart the centres are on each column - divided by that column\'s\n'
     '# own standard deviation, otherwise caffeine (0-500) would look important\n'
     '# next to sleep (4-9) just because its numbers are bigger\n'
     'centres = profile.drop(columns="members")\n'
     'spread = ((centres.max() - centres.min()) / num.std()).sort_values(ascending=False)\n'
     'print("\\nSpread between cluster centres, in standard deviations:")\n'
     'print(spread.round(3).to_string())'),

    ("17. Interpretations",
     'print("INTERPRETATIONS")\n'
     'print("-" * 66)\n'
     'print("1. Clustering is unsupervised - the file has no group column, so")\n'
     'print("   nothing here is being compared against a right answer. The")\n'
     'print("   metrics only describe the shape of the grouping, not its truth.")\n'
     'print("2. The inertia curve in question 10 bends gently rather than")\n'
     'print("   sharply, and the best silhouette in the whole sweep is only",\n'
     '      round(sweep["silhouette"].max(), 4))\n'
     'print("   at k =", sweep["silhouette"].idxmax(), "- a weak elbow and a low silhouette both say the")\n'
     'print("   same thing: these are soft regions, not separate islands.")\n'
     'print("   k = 3 was used anyway, because k = 2 only splits fast readers")\n'
     'print("   from slow ones while k = 3 also separates them by stress, which")\n'
     'print("   question 16 shows is a real difference worth keeping.")\n'
     'print("3. K-means scores best on all three measures - silhouette",\n'
     '      round(table.loc["K-means", "Silhouette"], 4))\n'
     'print("   That is expected: silhouette and Calinski-Harabasz both reward")\n'
     'print("   compact round clusters, which is exactly what k-means optimises.")\n'
     'print("   Judging k-means by them is slightly marking its own homework.")\n'
     'print("4. Agglomerative scores lowest - silhouette",\n'
     '      round(table.loc["Agglomerative", "Silhouette"], 4),\n'
     '      "- because ward linkage")\n'
     'print("   commits to every merge permanently: an early mistake cannot be")\n'
     'print("   undone, while k-means keeps reassigning until it settles.")\n'
     'print("5. Spectral lands between the two. Its graph-cutting approach pays")\n'
     'print("   off on curved or nested shapes; this data is a single diffuse")\n'
     'print("   cloud, so it has nothing unusual to find.")\n'
     'print("6. The clusters ARE interpretable even so. From question 16 the")\n'
     'print("   three columns that pull the centres apart are")\n'
     'print("  ", ", ".join(spread.index[:3]), "- between",\n'
     '      round(spread.iloc[2], 2), "and", round(spread.iloc[0], 2), "standard")\n'
     'print("   deviations each. Every other column is under",\n'
     '      round(spread.iloc[3] + 0.01, 1), "of a deviation.")\n'
     'print("   So the split is about how well a person performs and how")\n'
     'print("   stressed they are - age, sleep, screen time and caffeine")\n'
     'print("   barely move between clusters at all.")\n'
     'print("7. That explains the low silhouette. The grouping is real on three")\n'
     'print("   of the eight columns and close to noise on the other five, and")\n'
     'print("   the silhouette is computed over all eight at once. The clusters")\n'
     'print("   are meaningful; they are simply not well separated in full 8-D")\n'
     'print("   space, which is why the profile table matters more than the score.")'),
]

NB_CELLS = [
    ("md", "# Ex 7 \u2014 Clustering Techniques\n\n"
           "**Dataset:** Human Cognitive Performance Analysis  \n"
           "**No target column \u2014 this one is unsupervised**  \n**Reg No:** URK24CS1021"),
    ("code",
     "import numpy as np\n"
     "import pandas as pd\n"
     "import matplotlib.pyplot as plt\n"
     "import seaborn as sns\n"
     "from sklearn.preprocessing import StandardScaler\n"
     "from sklearn.decomposition import PCA\n"
     "from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering\n"
     "from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score\n\n"
     'sns.set_theme(style="whitegrid")\n'
     "SEED, K = 1021, 3\n\n"
     'df = pd.read_csv("cognitive.csv")\n'
     "df.head()"),
    ("code", "df.shape, df.isnull().sum().sum()"),
    ("code", "df.describe()"),
    ("md", "### Which columns, and why the run is sampled"),
    ("code",
     "# AI_Predicted_Score is a prediction OF Cognitive_Score - the same\n"
     "# information twice, and it would dominate every distance\n"
     'drop = ["User_ID", "AI_Predicted_Score", "Gender", "Diet_Type", "Exercise_Frequency"]\n\n'
     "# agglomerative and spectral build an n x n matrix; 80,000 rows is 6.4 billion cells\n"
     "sample = df.sample(n=2000, random_state=SEED)\n"
     "num = sample.drop(columns=drop)\n"
     "num.columns.tolist()"),
    ("code",
     "# caffeine 0-500 vs sleep 4-9: unscaled, distance would just mean caffeine\n"
     "X = StandardScaler().fit_transform(num)\n"
     "X.mean(axis=0).round(6), X.std(axis=0).round(6)"),
    ("md", "### How many clusters? \u2014 there is no label to ask"),
    ("code",
     "sweep = []\n"
     "for k in range(2, 9):\n"
     "    km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X)\n"
     '    sweep.append({"k": k, "inertia": km.inertia_,\n'
     '                  "silhouette": silhouette_score(X, km.labels_)})\n'
     'sweep = pd.DataFrame(sweep).set_index("k")\n'
     "sweep"),
    ("code",
     "fig, ax = plt.subplots(1, 2, figsize=(11, 4))\n"
     'sweep["inertia"].plot(ax=ax[0], marker="o", color="#4C72B0")\n'
     'ax[0].set_title("Elbow")\n'
     'sweep["silhouette"].plot(ax=ax[1], marker="o", color="#C44E52")\n'
     'ax[1].set_title("Silhouette")\n'
     "plt.show()"),
    ("md", "### Three algorithms, same data, same k"),
    ("code",
     "results, labels = [], {}\n\n"
     "def score(name, model):\n"
     "    lab = model.fit_predict(X)\n"
     "    labels[name] = lab\n"
     '    results.append({"Technique": name,\n'
     '                    "Silhouette": silhouette_score(X, lab),\n'
     '                    "Calinski-Harabasz": calinski_harabasz_score(X, lab),\n'
     '                    "Davies-Bouldin": davies_bouldin_score(X, lab)})\n'
     "    return lab\n\n"
     'score("K-means", KMeans(n_clusters=K, random_state=SEED, n_init=10))\n'
     "results[-1]"),
    ("code",
     'score("Agglomerative", AgglomerativeClustering(n_clusters=K, linkage="ward"))\n'
     "results[-1]"),
    ("code",
     'score("Spectral", SpectralClustering(n_clusters=K, random_state=SEED,\n'
     '                                     affinity="nearest_neighbors", n_neighbors=10))\n'
     "results[-1]"),
    ("md", "### Seeing 8 dimensions on a flat page"),
    ("code",
     "pcs = PCA(n_components=2, random_state=SEED).fit(X)\n"
     "XY = pcs.transform(X)\n"
     "pcs.explained_variance_ratio_.round(4)"),
    ("code",
     "fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True, sharey=True)\n"
     "for ax, (name, lab) in zip(axes, labels.items()):\n"
     '    ax.scatter(XY[:, 0], XY[:, 1], c=lab, cmap="viridis", s=10, alpha=0.7)\n'
     "    ax.set_title(name)\n"
     "plt.show()"),
    ("md", "### The comparison, and what the clusters mean"),
    ("code",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     "table"),
    ("code",
     "# a cluster number means nothing until you look inside it\n"
     'num.assign(cluster=labels["K-means"]).groupby("cluster").mean().round(2)'),
]

VIDEO = """# Ex 7 — Code explanation (teaching cues)
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
"""


def main() -> None:
    build(Exp(
        num=7, title=TITLE, date=DATE, out=OUT, aim=AIM,
        desc_label="Description (About Clustering)", desc=DESC, question=QUESTION,
        preamble=PREAMBLE, sections=SECTIONS, nb_cells=NB_CELLS, video=VIDEO,
        script_name="cognitive_clustering.py", notebook_name="Ex7_CognitiveClustering.ipynb",
        shot_command="python cognitive_clustering.py", shot_cwd=r"C:\DSE\Ex7",
    ))


if __name__ == "__main__":
    main()
