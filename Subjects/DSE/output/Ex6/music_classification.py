# Ex 6 - Classification Techniques
# URK24CS1021

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (6.5, 5)
pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 20)

SEED = 1021  # my reg no, so every run splits and seeds the same way
results = []  # every classifier appends its scores here for the final table

# 1. Import the dataset
# train.csv from the kaggle download - the only file with labels
df = pd.read_csv("music_genre.csv")
print("Rows loaded:", len(df))
print(df[["Artist Name", "Track Name", "Popularity", "Class"]].head())

# 2. Display the first 10 rows of the dataset
print(df.head(10))

# 3. Display the last 8 rows of the dataset
print(df.tail(8))

# 4. Information about the dataset
df.info()

# 5. Column names
print("Number of columns:", len(df.columns))
for i, col in enumerate(df.columns, 1):
    print(i, col)

# 6. Shape of the dataset and the class balance
print("Shape (rows, columns):", df.shape)
print("\nRows per class:")
print(df["Class"].value_counts().sort_index())
print("\nNumber of classes:", df["Class"].nunique())
print("Largest class share:", round(df["Class"].value_counts(normalize=True).max(), 4))

# 7. Statistical inferences
print(df.describe())

# 8. Data types
print(df.dtypes)
print("\nMissing values per column:")
print(df.isnull().sum()[df.isnull().sum() > 0])

# 9. Cleaning: the mixed-unit duration column
# "duration_in min/ms" is exactly what the name warns about - some rows are
# in minutes and some in milliseconds, in the same column
dur = df["duration_in min/ms"]
print("Rows that look like minutes (< 100):", (dur < 100).sum())
print("Rows that look like milliseconds   :", (dur >= 100).sum())

# put everything on one scale - minutes
df["duration_min"] = np.where(dur < 100, dur, dur / 60000)
print("\nAfter conversion:")
print(df["duration_min"].describe())

# 10. Cleaning: imputing the missing values
# three columns have real gaps, so fill each with its own median
for col in ["Popularity", "key", "instrumentalness"]:
    before = df[col].isnull().sum()
    df[col] = df[col].fillna(df[col].median())
    print(f"{col:<18} filled {before} missing values with the median")

print("\nMissing values left:", df.isnull().sum().sum())

# 11. Features, target and the train / test split
# artist and track name are free text and unique to almost every row, so
# they carry no pattern a classifier can generalise from
X = df.drop(columns=["Artist Name", "Track Name", "Class",
                     "duration_in min/ms", "duration_min"])
X["duration_min"] = df["duration_min"]
y = df["Class"]

# SVM is O(n^2) in the number of rows, so all five run on the same 5000-row
# sample - otherwise the comparison would not be like for like
idx = df.sample(n=5000, random_state=SEED).index
X, y = X.loc[idx], y.loc[idx]

# stratify keeps the class proportions identical in train and test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED, stratify=y)
print("Features:", list(X.columns))
print("\nTraining rows:", len(X_train), " Test rows:", len(X_test))

# 12. KNN Classification
# KNN measures distance, so the features must be scaled first or
# tempo (values near 120) would drown out danceability (0 to 1)
knn = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5))
knn.fit(X_train, y_train)
pred = knn.predict(X_test)
train_acc = accuracy_score(y_train, knn.predict(X_train))
test_acc = accuracy_score(y_test, pred)

print("Training accuracy:", round(train_acc, 4))
print("Test accuracy    :", round(test_acc, 4))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))
results.append({"Technique": "KNN", "Train Accuracy": train_acc,
                "Test Accuracy": test_acc})

sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d",
            cmap="Blues", cbar=False)
plt.title("KNN - confusion matrix")
plt.xlabel("Predicted class")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()

# 13. Decision Tree
# a tree splits on thresholds, so scaling makes no difference to it.
# max_depth caps the growth - an unlimited tree memorises the training set
tree = DecisionTreeClassifier(max_depth=10, random_state=SEED)
tree.fit(X_train, y_train)
pred = tree.predict(X_test)
train_acc = accuracy_score(y_train, tree.predict(X_train))
test_acc = accuracy_score(y_test, pred)

print("Training accuracy:", round(train_acc, 4))
print("Test accuracy    :", round(test_acc, 4))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))
results.append({"Technique": "Decision Tree", "Train Accuracy": train_acc,
                "Test Accuracy": test_acc})

sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d",
            cmap="Blues", cbar=False)
plt.title("Decision Tree - confusion matrix")
plt.xlabel("Predicted class")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()

# 14. Random Forest
# 200 trees, each on a random subset of rows and features, then a vote
forest = RandomForestClassifier(n_estimators=200, random_state=SEED)
forest.fit(X_train, y_train)
pred = forest.predict(X_test)
train_acc = accuracy_score(y_train, forest.predict(X_train))
test_acc = accuracy_score(y_test, pred)

print("Training accuracy:", round(train_acc, 4))
print("Test accuracy    :", round(test_acc, 4))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))
results.append({"Technique": "Random Forest", "Train Accuracy": train_acc,
                "Test Accuracy": test_acc})

sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d",
            cmap="Blues", cbar=False)
plt.title("Random Forest - confusion matrix")
plt.xlabel("Predicted class")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()

# 15. Logistic Regression
# a linear boundary per class - the simplest model in the comparison
logreg = make_pipeline(StandardScaler(),
                       LogisticRegression(max_iter=2000, random_state=SEED))
logreg.fit(X_train, y_train)
pred = logreg.predict(X_test)
train_acc = accuracy_score(y_train, logreg.predict(X_train))
test_acc = accuracy_score(y_test, pred)

print("Training accuracy:", round(train_acc, 4))
print("Test accuracy    :", round(test_acc, 4))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))
results.append({"Technique": "Logistic Regression", "Train Accuracy": train_acc,
                "Test Accuracy": test_acc})

sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d",
            cmap="Blues", cbar=False)
plt.title("Logistic Regression - confusion matrix")
plt.xlabel("Predicted class")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()

# 16. Support Vector Machine
# rbf kernel, so the boundary can curve. distance based again, so scaled
svm = make_pipeline(StandardScaler(), SVC(kernel="rbf", random_state=SEED))
svm.fit(X_train, y_train)
pred = svm.predict(X_test)
train_acc = accuracy_score(y_train, svm.predict(X_train))
test_acc = accuracy_score(y_test, pred)

print("Training accuracy:", round(train_acc, 4))
print("Test accuracy    :", round(test_acc, 4))
print("\nClassification report:")
print(classification_report(y_test, pred, zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(y_test, pred))
results.append({"Technique": "SVM", "Train Accuracy": train_acc,
                "Test Accuracy": test_acc})

sns.heatmap(confusion_matrix(y_test, pred), annot=True, fmt="d",
            cmap="Blues", cbar=False)
plt.title("SVM - confusion matrix")
plt.xlabel("Predicted class")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()

# 17. Comparative table of accuracy
table = pd.DataFrame(results).set_index("Technique").round(4)
table["Gap (overfit)"] = (table["Train Accuracy"] - table["Test Accuracy"]).round(4)
print(table.to_string())
print("\nBest test accuracy:", table["Test Accuracy"].idxmax(),
      "->", round(table["Test Accuracy"].max(), 4))
print("Widest train-test gap:", table["Gap (overfit)"].idxmax(),
      "->", round(table["Gap (overfit)"].max(), 4))

table[["Train Accuracy", "Test Accuracy"]].plot(kind="bar", rot=20,
                                                color=["#B0B0B0", "#4C72B0"])
plt.ylabel("Accuracy")
plt.title("Training vs test accuracy by classifier")
plt.tight_layout()
plt.show()

# 18. Interpretations on classification, overfitting and underfitting
baseline = y_test.value_counts(normalize=True).max()
print("INTERPRETATIONS")
print("-" * 64)
print("1. This is an 11-class problem and the classes are not balanced.")
print("   Always guessing the largest class would already score",
      round(baseline, 4), "-")
print("   that is the number every classifier here has to beat.")
print("2. Best test accuracy:", table["Test Accuracy"].idxmax(), "at",
      round(table["Test Accuracy"].max(), 4), "- roughly double the")
print("   baseline, so the audio features do carry real genre signal.")
print("3. OVERFITTING - Random Forest scores",
      round(table.loc["Random Forest", "Train Accuracy"], 4), "on training data")
print("   and", round(table.loc["Random Forest", "Test Accuracy"], 4),
      "on unseen data, a gap of",
      round(table.loc["Random Forest", "Gap (overfit)"], 4))
print("   Fully grown trees memorise every training row, so the forest")
print("   knows the training set far better than it knows music.")
print("4. UNDERFITTING - Logistic Regression scores",
      round(table.loc["Logistic Regression", "Train Accuracy"], 4), "on training")
print("   data and", round(table.loc["Logistic Regression", "Test Accuracy"], 4),
      "on test - no better on rows it has already seen.")
print("   It is not memorising anything, it simply cannot fit the data:")
print("   one straight boundary per class is too rigid for 11 genres")
print("   that overlap.")
print("5. The healthy middle is the small gap, not the high training score.")
print("   SVM sits closest to it and generalises about as well as the")
print("   forest while learning far less of the noise.")
print("6. The confusion matrices show the errors are not spread evenly -")
print("   the large classes absorb predictions from the small ones, which")
print("   is exactly what imbalance does to a classifier.")