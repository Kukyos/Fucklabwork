# Ex 7 - Clustering Techniques
# URK24CS1021

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import (KMeans, AgglomerativeClustering,
                             SpectralClustering)
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score)

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (7, 4.5)
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)

SEED = 1021  # my reg no, so every run samples and seeds the same way
K = 3        # chosen in question 10, below
results = []  # every algorithm appends its metrics here for the final table
labels = {}   # and its cluster labels, for the comparison plot

# 1. Import the dataset
df = pd.read_csv("cognitive.csv")
print("Rows loaded:", len(df))
print(df[["User_ID", "Age", "Sleep_Duration", "Reaction_Time",
          "Cognitive_Score"]].head())

# 2. Display the first 10 rows of the dataset
print(df.head(10).to_string())

# 3. Display the last 8 rows of the dataset
print(df.tail(8).to_string())

# 4. Information about the dataset
df.info()

# 5. Column names
print("Number of columns:", len(df.columns))
for i, col in enumerate(df.columns, 1):
    print(i, col)

# 6. Shape of the dataset
print("Shape (rows, columns):", df.shape)
print("Rows   :", df.shape[0])
print("Columns:", df.shape[1])
print("\nCounts for the three text columns:")
for col in ["Gender", "Diet_Type", "Exercise_Frequency"]:
    print(col, "->", df[col].value_counts().to_dict())

# 7. Statistical inferences
print(df.describe().to_string())
print("\nMissing values in the whole file:", df.isnull().sum().sum())

# 8. Data types
print(df.dtypes)
print("\nNumeric columns:", list(df.select_dtypes(include="number").columns))

# 9. Choosing the features, sampling and scaling
# User_ID is a unique key, not a measurement.
# AI_Predicted_Score is a model's prediction OF Cognitive_Score - keeping it
# would mean feeding the same information in twice and letting it dominate
# every distance.
drop = ["User_ID", "AI_Predicted_Score", "Gender", "Diet_Type", "Exercise_Frequency"]

# agglomerative and spectral clustering both build an n x n matrix of
# distances between every pair of rows. at 80,000 rows that is 6.4 billion
# entries, so all three algorithms run on the same 2000-row sample.
sample = df.sample(n=2000, random_state=SEED)
num = sample.drop(columns=drop)
print("Clustering on:", list(num.columns))
print("Sample shape :", num.shape)

# caffeine runs 0-500 and sleep 4-9, so without scaling "distance" would
# mean "difference in caffeine" and nothing else
X = StandardScaler().fit_transform(num)
print("\nBefore scaling (mean / std):")
print(num.agg(["mean", "std"]).round(2).to_string())
print("\nAfter scaling, every column has mean 0 and std 1:",
      np.allclose(X.mean(axis=0), 0), np.allclose(X.std(axis=0), 1))

# 10. Choosing the number of clusters
# there is no label to check against, so k has to be argued for.
# elbow = where extra clusters stop reducing the within-cluster spread
sweep = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X)
    sweep.append({"k": k, "inertia": km.inertia_,
                  "silhouette": silhouette_score(X, km.labels_)})
sweep = pd.DataFrame(sweep).set_index("k")
print(sweep.round(4).to_string())
print("\nBest silhouette at k =", sweep["silhouette"].idxmax())

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
sweep["inertia"].plot(ax=ax[0], marker="o", color="#4C72B0")
ax[0].set_title("Elbow - within-cluster sum of squares")
ax[0].set_xlabel("k")
sweep["silhouette"].plot(ax=ax[1], marker="o", color="#C44E52")
ax[1].set_title("Silhouette score")
ax[1].set_xlabel("k")
plt.tight_layout()
plt.show()

# 11. K-means clustering
# k-means: place K centres, assign each point to the nearest, move the
# centres to the mean of what they caught, repeat until nothing moves
km = KMeans(n_clusters=K, random_state=SEED, n_init=10)
labels["K-means"] = km.fit_predict(X)
lab = labels["K-means"]

print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())
print("Iterations to converge:", km.n_iter_)
print("Inertia:", round(km.inertia_, 2))
print("\nSilhouette       :", round(silhouette_score(X, lab), 4))
print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))
print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))
results.append({"Technique": "K-means",
                "Silhouette": silhouette_score(X, lab),
                "Calinski-Harabasz": calinski_harabasz_score(X, lab),
                "Davies-Bouldin": davies_bouldin_score(X, lab)})

# 12. Agglomerative Clustering
# bottom-up: start with 2000 clusters of one point each and keep merging
# the two closest, using ward linkage, until only K are left
agg = AgglomerativeClustering(n_clusters=K, linkage="ward")
labels["Agglomerative"] = agg.fit_predict(X)
lab = labels["Agglomerative"]

print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())
print("\nSilhouette       :", round(silhouette_score(X, lab), 4))
print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))
print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))
results.append({"Technique": "Agglomerative",
                "Silhouette": silhouette_score(X, lab),
                "Calinski-Harabasz": calinski_harabasz_score(X, lab),
                "Davies-Bouldin": davies_bouldin_score(X, lab)})

# 13. Spectral Clustering
# builds a nearest-neighbour graph of the points and cuts it where the
# connections are weakest, so it can follow shapes k-means cannot
spec = SpectralClustering(n_clusters=K, random_state=SEED,
                          affinity="nearest_neighbors", n_neighbors=10)
labels["Spectral"] = spec.fit_predict(X)
lab = labels["Spectral"]

print("Cluster sizes:", pd.Series(lab).value_counts().sort_index().to_dict())
print("\nSilhouette       :", round(silhouette_score(X, lab), 4))
print("Calinski-Harabasz:", round(calinski_harabasz_score(X, lab), 2))
print("Davies-Bouldin   :", round(davies_bouldin_score(X, lab), 4))
results.append({"Technique": "Spectral",
                "Silhouette": silhouette_score(X, lab),
                "Calinski-Harabasz": calinski_harabasz_score(X, lab),
                "Davies-Bouldin": davies_bouldin_score(X, lab)})

# 14. Display the clusters for all three techniques
# the data has 8 dimensions and a page has 2, so PCA compresses it down to
# the two directions that carry the most variation, purely for drawing
pcs = PCA(n_components=2, random_state=SEED).fit(X)
XY = pcs.transform(X)
print("Variation kept by the two components:",
      pcs.explained_variance_ratio_.round(4),
      "->", round(pcs.explained_variance_ratio_.sum(), 4))

fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True, sharey=True)
for ax, (name, lab) in zip(axes, labels.items()):
    ax.scatter(XY[:, 0], XY[:, 1], c=lab, cmap="viridis", s=10, alpha=0.7)
    ax.set_title(name)
    ax.set_xlabel("PC 1")
axes[0].set_ylabel("PC 2")
plt.tight_layout()
plt.show()

# 15. Comparative table of performance metrics
table = pd.DataFrame(results).set_index("Technique").round(4)
print(table.to_string())
print("\nHigher is better: Silhouette, Calinski-Harabasz")
print("Lower is better : Davies-Bouldin")
print("\nBest silhouette        :", table["Silhouette"].idxmax())
print("Best Calinski-Harabasz :", table["Calinski-Harabasz"].idxmax())
print("Best Davies-Bouldin    :", table["Davies-Bouldin"].idxmin())

fig, ax = plt.subplots(1, 3, figsize=(13, 4))
for a, col, colour in zip(ax, table.columns, ["#4C72B0", "#55A868", "#C44E52"]):
    table[col].plot(kind="bar", ax=a, color=colour, rot=20)
    a.set_title(col)
    a.set_xlabel("")
plt.tight_layout()
plt.show()

# 16. What the clusters actually mean
# a cluster number means nothing on its own - look at the averages inside it
profile = num.assign(cluster=labels["K-means"]).groupby("cluster").mean().round(2)
profile["members"] = pd.Series(labels["K-means"]).value_counts().sort_index()
print(profile.to_string())

# how far apart the centres are on each column - divided by that column's
# own standard deviation, otherwise caffeine (0-500) would look important
# next to sleep (4-9) just because its numbers are bigger
centres = profile.drop(columns="members")
spread = ((centres.max() - centres.min()) / num.std()).sort_values(ascending=False)
print("\nSpread between cluster centres, in standard deviations:")
print(spread.round(3).to_string())

# 17. Interpretations
print("INTERPRETATIONS")
print("-" * 66)
print("1. Clustering is unsupervised - the file has no group column, so")
print("   nothing here is being compared against a right answer. The")
print("   metrics only describe the shape of the grouping, not its truth.")
print("2. The inertia curve in question 10 bends gently rather than")
print("   sharply, and the best silhouette in the whole sweep is only",
      round(sweep["silhouette"].max(), 4))
print("   at k =", sweep["silhouette"].idxmax(), "- a weak elbow and a low silhouette both say the")
print("   same thing: these are soft regions, not separate islands.")
print("   k = 3 was used anyway, because k = 2 only splits fast readers")
print("   from slow ones while k = 3 also separates them by stress, which")
print("   question 16 shows is a real difference worth keeping.")
print("3. K-means scores best on all three measures - silhouette",
      round(table.loc["K-means", "Silhouette"], 4))
print("   That is expected: silhouette and Calinski-Harabasz both reward")
print("   compact round clusters, which is exactly what k-means optimises.")
print("   Judging k-means by them is slightly marking its own homework.")
print("4. Agglomerative scores lowest - silhouette",
      round(table.loc["Agglomerative", "Silhouette"], 4),
      "- because ward linkage")
print("   commits to every merge permanently: an early mistake cannot be")
print("   undone, while k-means keeps reassigning until it settles.")
print("5. Spectral lands between the two. Its graph-cutting approach pays")
print("   off on curved or nested shapes; this data is a single diffuse")
print("   cloud, so it has nothing unusual to find.")
print("6. The clusters ARE interpretable even so. From question 16 the")
print("   three columns that pull the centres apart are")
print("  ", ", ".join(spread.index[:3]), "- between",
      round(spread.iloc[2], 2), "and", round(spread.iloc[0], 2), "standard")
print("   deviations each. Every other column is under",
      round(spread.iloc[3] + 0.01, 1), "of a deviation.")
print("   So the split is about how well a person performs and how")
print("   stressed they are - age, sleep, screen time and caffeine")
print("   barely move between clusters at all.")
print("7. That explains the low silhouette. The grouping is real on three")
print("   of the eight columns and close to noise on the other five, and")
print("   the silhouette is computed over all eight at once. The clusters")
print("   are meaningful; they are simply not well separated in full 8-D")
print("   space, which is why the profile table matters more than the score.")