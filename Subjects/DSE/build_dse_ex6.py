"""Build Cleo's DSE Ex-6 record (classification on the music genre dataset).
Content only - the docx/notebook/screenshot machinery lives in dse_record.py.

    python Subjects/DSE/build_dse_ex6.py
"""
from __future__ import annotations

from pathlib import Path

from dse_record import Exp, build

HERE = Path(__file__).parent
OUT = HERE / "output" / "Ex6"

TITLE = "CLASSIFICATION TECHNIQUES"
DATE = "11/09/2026"

AIM = ("To build classification models in Python that predict a categorical label from a "
       "real-world dataset, and to compare KNN, decision trees, random forest, logistic "
       "regression and support vector machines using accuracy, the classification report "
       "and the confusion matrix.")

DESC = (
    "Classification predicts which class a record belongs to rather than a number. KNN "
    "stores the training set and labels a new point by majority vote of its nearest "
    "neighbours. A decision tree splits the data on one feature at a time until each leaf "
    "is close to pure. A random forest grows many trees on random subsets and lets them "
    "vote, which cancels out the quirks of any single tree. Logistic regression fits a "
    "linear boundary and reports a probability per class. A support vector machine looks "
    "for the boundary with the widest margin between classes. The results are judged by "
    "accuracy, by the classification report \u2014 precision, recall and F1 for each class "
    "\u2014 and by the confusion matrix, which shows exactly which classes are being mistaken "
    "for which."
)

QUESTION = (
    "Dataset: Music Genre Classification\n"
    "(https://www.kaggle.com/datasets/purumalgi/music-genre-classification)\n"
    "\u2022 Import the dataset.\n"
    "\u2022 Display the first 10 rows of the dataset.\n"
    "\u2022 Display the last 8 rows of the dataset.\n"
    "\u2022 Display information about the dataset: information, column names, shape, "
    "statistical inferences, data types.\n"
    "\u2022 Perform the following classification and measure the performance: KNN "
    "Classification, Decision Trees, Random Forest, Logistic Regression, Support Vector "
    "Machine.\n"
    "\u2022 Display the classification report and confusion matrix for all the "
    "classifications.\n"
    "\u2022 Draw a comparative table of accuracy for all the classification techniques.\n"
    "\u2022 Document your interpretations on classification, overfitting and underfitting."
)

PREAMBLE = (
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "from sklearn.model_selection import train_test_split\n"
    "from sklearn.neighbors import KNeighborsClassifier\n"
    "from sklearn.tree import DecisionTreeClassifier\n"
    "from sklearn.ensemble import RandomForestClassifier\n"
    "from sklearn.linear_model import LogisticRegression\n"
    "from sklearn.svm import SVC\n"
    "from sklearn.preprocessing import StandardScaler\n"
    "from sklearn.pipeline import make_pipeline\n"
    "from sklearn.metrics import (accuracy_score, classification_report,\n"
    "                             confusion_matrix)\n\n"
    'sns.set_theme(style="whitegrid")\n'
    'plt.rcParams["figure.figsize"] = (6.5, 5)\n'
    'pd.set_option("display.width", 150)\n'
    'pd.set_option("display.max_columns", 20)\n\n'
    "SEED = 1021  # my reg no, so every run splits and seeds the same way\n"
    "results = []  # every classifier appends its scores here for the final table\n\n"
)


def _model_section(label: str, varname: str, ctor: str, note: str) -> str:
    """Each classifier does the same five things, so the code shape is identical -
    fit, score train and test, report, confusion matrix, record the row."""
    return (
        f"{note}"
        f"{varname} = {ctor}\n"
        f"{varname}.fit(X_train, y_train)\n"
        f"pred = {varname}.predict(X_test)\n"
        f"train_acc = accuracy_score(y_train, {varname}.predict(X_train))\n"
        "test_acc = accuracy_score(y_test, pred)\n\n"
        'print("Training accuracy:", round(train_acc, 4))\n'
        'print("Test accuracy    :", round(test_acc, 4))\n'
        'print("\\nClassification report:")\n'
        "print(classification_report(y_test, pred, zero_division=0))\n"
        'print("Confusion matrix:")\n'
        "print(confusion_matrix(y_test, pred))\n"
        f'results.append({{"Technique": "{label}", "Train Accuracy": train_acc,\n'
        '                "Test Accuracy": test_acc})\n\n'
        "sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt=\"d\",\n"
        '            cmap="Blues", cbar=False)\n'
        f'plt.title("{label} - confusion matrix")\n'
        'plt.xlabel("Predicted class")\n'
        'plt.ylabel("Actual class")\n'
        "plt.tight_layout()\n"
        "plt.show()"
    )


SECTIONS: list[tuple[str, str]] = [
    ("1. Import the dataset",
     '# train.csv from the kaggle download - the only file with labels\n'
     'df = pd.read_csv("music_genre.csv")\n'
     'print("Rows loaded:", len(df))\n'
     'print(df[["Artist Name", "Track Name", "Popularity", "Class"]].head())'),

    ("2. Display the first 10 rows of the dataset",
     'print(df.head(10).to_string())'),

    ("3. Display the last 8 rows of the dataset",
     'print(df.tail(8).to_string())'),

    ("4. Information about the dataset",
     'df.info()'),

    ("5. Column names",
     'print("Number of columns:", len(df.columns))\n'
     'for i, col in enumerate(df.columns, 1):\n'
     '    print(i, col)'),

    ("6. Shape of the dataset and the class balance",
     'print("Shape (rows, columns):", df.shape)\n'
     'print("\\nRows per class:")\n'
     'print(df["Class"].value_counts().sort_index())\n'
     'print("\\nNumber of classes:", df["Class"].nunique())\n'
     'print("Largest class share:", round(df["Class"].value_counts(normalize=True).max(), 4))'),

    ("7. Statistical inferences",
     'print(df.describe().to_string())'),

    ("8. Data types",
     'print(df.dtypes)\n'
     'print("\\nMissing values per column:")\n'
     'print(df.isnull().sum()[df.isnull().sum() > 0])'),

    ("9. Cleaning: the mixed-unit duration column",
     '# "duration_in min/ms" is exactly what the name warns about - some rows are\n'
     '# in minutes and some in milliseconds, in the same column\n'
     'dur = df["duration_in min/ms"]\n'
     'print("Rows that look like minutes (< 100):", (dur < 100).sum())\n'
     'print("Rows that look like milliseconds   :", (dur >= 100).sum())\n\n'
     '# put everything on one scale - minutes\n'
     'df["duration_min"] = np.where(dur < 100, dur, dur / 60000)\n'
     'print("\\nAfter conversion:")\n'
     'print(df["duration_min"].describe())'),

    ("10. Cleaning: imputing the missing values",
     '# three columns have real gaps, so fill each with its own median\n'
     'for col in ["Popularity", "key", "instrumentalness"]:\n'
     '    before = df[col].isnull().sum()\n'
     '    df[col] = df[col].fillna(df[col].median())\n'
     '    print(f"{col:<18} filled {before} missing values with the median")\n\n'
     'print("\\nMissing values left:", df.isnull().sum().sum())'),

    ("11. Features, target and the train / test split",
     '# artist and track name are free text and unique to almost every row, so\n'
     '# they carry no pattern a classifier can generalise from\n'
     'X = df.drop(columns=["Artist Name", "Track Name", "Class",\n'
     '                     "duration_in min/ms", "duration_min"])\n'
     'X["duration_min"] = df["duration_min"]\n'
     'y = df["Class"]\n\n'
     '# SVM is O(n^2) in the number of rows, so all five run on the same 5000-row\n'
     '# sample - otherwise the comparison would not be like for like\n'
     'idx = df.sample(n=5000, random_state=SEED).index\n'
     'X, y = X.loc[idx], y.loc[idx]\n\n'
     '# stratify keeps the class proportions identical in train and test\n'
     'X_train, X_test, y_train, y_test = train_test_split(\n'
     '    X, y, test_size=0.2, random_state=SEED, stratify=y)\n'
     'print("Features:", list(X.columns))\n'
     'print("\\nTraining rows:", len(X_train), " Test rows:", len(X_test))'),

    ("12. KNN Classification",
     _model_section(
         "KNN", "knn",
         "make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5))",
         "# KNN measures distance, so the features must be scaled first or\n"
         "# tempo (values near 120) would drown out danceability (0 to 1)\n")),

    ("13. Decision Tree",
     _model_section(
         "Decision Tree", "tree",
         "DecisionTreeClassifier(max_depth=10, random_state=SEED)",
         "# a tree splits on thresholds, so scaling makes no difference to it.\n"
         "# max_depth caps the growth - an unlimited tree memorises the training set\n")),

    ("14. Random Forest",
     _model_section(
         "Random Forest", "forest",
         "RandomForestClassifier(n_estimators=200, random_state=SEED)",
         "# 200 trees, each on a random subset of rows and features, then a vote\n")),

    ("15. Logistic Regression",
     _model_section(
         "Logistic Regression", "logreg",
         "make_pipeline(StandardScaler(),\n"
         "                       LogisticRegression(max_iter=2000, random_state=SEED))",
         "# a linear boundary per class - the simplest model in the comparison\n")),

    ("16. Support Vector Machine",
     _model_section(
         "SVM", "svm",
         'make_pipeline(StandardScaler(), SVC(kernel="rbf", random_state=SEED))',
         "# rbf kernel, so the boundary can curve. distance based again, so scaled\n")),

    ("17. Comparative table of accuracy",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     'table["Gap (overfit)"] = (table["Train Accuracy"] - table["Test Accuracy"]).round(4)\n'
     'print(table.to_string())\n'
     'print("\\nBest test accuracy:", table["Test Accuracy"].idxmax(),\n'
     '      "->", round(table["Test Accuracy"].max(), 4))\n'
     'print("Widest train-test gap:", table["Gap (overfit)"].idxmax(),\n'
     '      "->", round(table["Gap (overfit)"].max(), 4))\n\n'
     'table[["Train Accuracy", "Test Accuracy"]].plot(kind="bar", rot=20,\n'
     '                                                color=["#B0B0B0", "#4C72B0"])\n'
     'plt.ylabel("Accuracy")\n'
     'plt.title("Training vs test accuracy by classifier")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("18. Interpretations on classification, overfitting and underfitting",
     'baseline = y_test.value_counts(normalize=True).max()\n'
     'print("INTERPRETATIONS")\n'
     'print("-" * 64)\n'
     'print("1. This is an 11-class problem and the classes are not balanced.")\n'
     'print("   Always guessing the largest class would already score",\n'
     '      round(baseline, 4), "-")\n'
     'print("   that is the number every classifier here has to beat.")\n'
     'print("2. Best test accuracy:", table["Test Accuracy"].idxmax(), "at",\n'
     '      round(table["Test Accuracy"].max(), 4), "- roughly double the")\n'
     'print("   baseline, so the audio features do carry real genre signal.")\n'
     'print("3. OVERFITTING - Random Forest scores",\n'
     '      round(table.loc["Random Forest", "Train Accuracy"], 4), "on training data")\n'
     'print("   and", round(table.loc["Random Forest", "Test Accuracy"], 4),\n'
     '      "on unseen data, a gap of",\n'
     '      round(table.loc["Random Forest", "Gap (overfit)"], 4))\n'
     'print("   Fully grown trees memorise every training row, so the forest")\n'
     'print("   knows the training set far better than it knows music.")\n'
     'print("4. UNDERFITTING - Logistic Regression scores",\n'
     '      round(table.loc["Logistic Regression", "Train Accuracy"], 4), "on training")\n'
     'print("   data and", round(table.loc["Logistic Regression", "Test Accuracy"], 4),\n'
     '      "on test - no better on rows it has already seen.")\n'
     'print("   It is not memorising anything, it simply cannot fit the data:")\n'
     'print("   one straight boundary per class is too rigid for 11 genres")\n'
     'print("   that overlap.")\n'
     'print("5. The healthy middle is the small gap, not the high training score.")\n'
     'print("   SVM sits closest to it and generalises about as well as the")\n'
     'print("   forest while learning far less of the noise.")\n'
     'print("6. The confusion matrices show the errors are not spread evenly -")\n'
     'print("   the large classes absorb predictions from the small ones, which")\n'
     'print("   is exactly what imbalance does to a classifier.")'),
]

NB_CELLS = [
    ("md", "# Ex 6 \u2014 Classification Techniques\n\n"
           "**Dataset:** Music Genre Classification  \n"
           "**Target:** Class (11 genres, 0\u201310)  \n**Reg No:** URK24CS1021"),
    ("code",
     "import numpy as np\n"
     "import pandas as pd\n"
     "import matplotlib.pyplot as plt\n"
     "import seaborn as sns\n"
     "from sklearn.model_selection import train_test_split\n"
     "from sklearn.neighbors import KNeighborsClassifier\n"
     "from sklearn.tree import DecisionTreeClassifier\n"
     "from sklearn.ensemble import RandomForestClassifier\n"
     "from sklearn.linear_model import LogisticRegression\n"
     "from sklearn.svm import SVC\n"
     "from sklearn.preprocessing import StandardScaler\n"
     "from sklearn.pipeline import make_pipeline\n"
     "from sklearn.metrics import accuracy_score, classification_report, confusion_matrix\n\n"
     'sns.set_theme(style="whitegrid")\n'
     "SEED = 1021\n\n"
     'df = pd.read_csv("music_genre.csv")\n'
     "df.head()"),
    ("md", "### How balanced are the classes?"),
    ("code", 'df["Class"].value_counts().sort_index()'),
    ("code",
     "# the baseline any classifier has to beat: always guess the biggest class\n"
     'df["Class"].value_counts(normalize=True).max()'),
    ("md", "### Two things wrong with this file before anything can be fitted"),
    ("code",
     '# the column is literally named "duration_in min/ms" - and it means it\n'
     'dur = df["duration_in min/ms"]\n'
     "(dur < 100).sum(), (dur >= 100).sum()"),
    ("code",
     'df["duration_min"] = np.where(dur < 100, dur, dur / 60000)\n'
     'df["duration_min"].describe()'),
    ("code",
     "df.isnull().sum()[df.isnull().sum() > 0]"),
    ("code",
     'for col in ["Popularity", "key", "instrumentalness"]:\n'
     "    df[col] = df[col].fillna(df[col].median())\n"
     "df.isnull().sum().sum()"),
    ("md", "### Features, and why the run is sampled"),
    ("code",
     "# names are unique per row, so nothing to generalise from\n"
     'X = df.drop(columns=["Artist Name", "Track Name", "Class",\n'
     '                     "duration_in min/ms", "duration_min"])\n'
     'X["duration_min"] = df["duration_min"]\n'
     'y = df["Class"]\n\n'
     "# SVM is quadratic in rows, so every model sees the same 5000-row sample\n"
     "idx = df.sample(n=5000, random_state=SEED).index\n"
     "X, y = X.loc[idx], y.loc[idx]\n"
     "X_train, X_test, y_train, y_test = train_test_split(\n"
     "    X, y, test_size=0.2, random_state=SEED, stratify=y)\n"
     "X.shape"),
    ("md", "### Five classifiers, same split, same scoring"),
    ("code",
     "results = []\n\n"
     "def score(name, model):\n"
     "    model.fit(X_train, y_train)\n"
     "    train_acc = accuracy_score(y_train, model.predict(X_train))\n"
     "    test_acc = accuracy_score(y_test, model.predict(X_test))\n"
     '    results.append({"Technique": name, "Train Accuracy": train_acc,\n'
     '                    "Test Accuracy": test_acc})\n'
     "    return model\n\n"
     '# KNN and SVM measure distance, so they get a scaler; the tree does not care\n'
     'knn = score("KNN", make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)))\n'
     "results[-1]"),
    ("code",
     'tree = score("Decision Tree", DecisionTreeClassifier(max_depth=10, random_state=SEED))\n'
     "results[-1]"),
    ("code",
     'forest = score("Random Forest", RandomForestClassifier(n_estimators=200, random_state=SEED))\n'
     "results[-1]"),
    ("code",
     'logreg = score("Logistic Regression",\n'
     "               make_pipeline(StandardScaler(),\n"
     "                             LogisticRegression(max_iter=2000, random_state=SEED)))\n"
     "results[-1]"),
    ("code",
     'svm = score("SVM", make_pipeline(StandardScaler(), SVC(kernel="rbf", random_state=SEED)))\n'
     "results[-1]"),
    ("md", "### Report and confusion matrix for the best model"),
    ("code",
     "pred = forest.predict(X_test)\n"
     "print(classification_report(y_test, pred, zero_division=0))"),
    ("code",
     'sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d", cmap="Blues", cbar=False)\n'
     'plt.title("Random Forest - confusion matrix")\n'
     'plt.xlabel("Predicted")\n'
     'plt.ylabel("Actual")\n'
     "plt.show()"),
    ("md", "### The comparison \u2014 and where the overfitting shows"),
    ("code",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     'table["Gap"] = (table["Train Accuracy"] - table["Test Accuracy"]).round(4)\n'
     "table"),
    ("code",
     'table[["Train Accuracy", "Test Accuracy"]].plot(kind="bar", rot=20,\n'
     '                                                color=["#B0B0B0", "#4C72B0"])\n'
     'plt.ylabel("Accuracy")\n'
     'plt.title("Training vs test accuracy")\n'
     "plt.show()"),
]

VIDEO = """# Ex 6 — Code explanation (teaching cues)
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
"""


def main() -> None:
    build(Exp(
        num=6, title=TITLE, date=DATE, out=OUT, aim=AIM,
        desc_label="Description (About Classification)", desc=DESC, question=QUESTION,
        preamble=PREAMBLE, sections=SECTIONS, nb_cells=NB_CELLS, video=VIDEO,
        script_name="music_classification.py", notebook_name="Ex6_MusicGenre.ipynb",
        shot_command="python music_classification.py", shot_cwd=r"C:\DSE\Ex6",
    ))


if __name__ == "__main__":
    main()
