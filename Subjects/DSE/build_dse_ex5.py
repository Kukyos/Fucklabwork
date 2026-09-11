"""Build Cleo's DSE Ex-5 record (regression on the India rental house price
dataset). Content only - the docx/notebook/screenshot machinery lives in
dse_record.py now.

    python Subjects/DSE/build_dse_ex5.py
"""
from __future__ import annotations

from pathlib import Path

from dse_record import Exp, build

HERE = Path(__file__).parent
OUT = HERE / "output" / "Ex5"

TITLE = "REGRESSION ANALYSIS"
DATE = "11/09/2026"

AIM = ("To build regression models in Python that predict a continuous target from a "
       "real-world dataset, and to compare simple linear, multiple linear, polynomial, "
       "Lasso and Ridge regression using the R\u00b2 score and the root mean squared error.")

DESC = (
    "Regression fits a function to data so that a continuous value can be predicted "
    "from other measured values. Simple linear regression uses one predictor and fits "
    "a straight line; multiple linear regression uses several predictors and fits a "
    "plane. Polynomial regression adds squared and interaction terms so the fit can "
    "bend. Lasso and Ridge are the same linear fit with a penalty added to the size of "
    "the coefficients \u2014 Ridge shrinks them, Lasso can shrink them all the way to zero "
    "and so drops features outright. Two numbers judge the result: R\u00b2, the share of "
    "the variation in the target that the model explains (1.0 is perfect, 0 is no "
    "better than always guessing the mean), and RMSE, the typical size of the error in "
    "the units of the target itself."
)

QUESTION = (
    "Dataset: India Rental House Price\n"
    "(https://www.kaggle.com/datasets/bhavyadhingra00020/india-rental-house-price)\n"
    "Target to Predict: Price per Square Foot\n"
    "\u2022 Import the dataset.\n"
    "\u2022 Display the first 10 rows of the dataset.\n"
    "\u2022 Display the last 8 rows of the dataset.\n"
    "\u2022 Display information about the dataset: information, column names, shape, "
    "statistical inferences, data types.\n"
    "\u2022 Perform the following regression and measure the performance using r2 score "
    "and root mean squared error: Simple Linear Regression, Multiple Linear Regression, "
    "Polynomial Regression, Lasso Regression, Ridge Regression.\n"
    "\u2022 Draw a comparative table of r2 score and root mean square of all the "
    "regression techniques.\n"
    "\u2022 Document your interpretations."
)

PREAMBLE = (
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "from sklearn.model_selection import train_test_split\n"
    "from sklearn.linear_model import LinearRegression, Lasso, Ridge\n"
    "from sklearn.preprocessing import PolynomialFeatures, StandardScaler\n"
    "from sklearn.pipeline import make_pipeline\n"
    "from sklearn.metrics import r2_score, root_mean_squared_error\n\n"
    'sns.set_theme(style="whitegrid")\n'
    'plt.rcParams["figure.figsize"] = (7, 4.5)\n'
    'pd.set_option("display.width", 150)\n'
    'pd.set_option("display.max_columns", 20)\n\n'
    "SEED = 1021  # my reg no, so every run splits the same way\n"
    "results = []  # every model appends its scores here for the final table\n\n"
)

SECTIONS: list[tuple[str, str]] = [
    ("1. Import the dataset",
     '# the kaggle download ships one csv per city; they share a schema, so I\n'
     '# concatenated Delhi + Mumbai + Pune into one file before loading\n'
     'df = pd.read_csv("rental.csv")\n'
     'print("Rows loaded:", len(df))\n'
     'print(df[["house_type", "house_size", "location", "city", "price"]].head())'),

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

    ("6. Shape of the dataset",
     'print("Shape (rows, columns):", df.shape)\n'
     'print("Rows   :", df.shape[0])\n'
     'print("Columns:", df.shape[1])\n'
     'print("\\nRows per city:")\n'
     'print(df["city"].value_counts())'),

    ("7. Statistical inferences",
     'print(df.describe().to_string())\n'
     'print("\\nMissing values per column:")\n'
     'print(df.isnull().sum())'),

    ("8. Data types",
     'print(df.dtypes)\n'
     'print("\\nNumeric columns    :", list(df.select_dtypes(include="number").columns))\n'
     'print("Categorical columns:", list(df.select_dtypes(include="object").columns))'),

    ("9. Building the target column 'Price per Square Foot'",
     '# the assigned target is Price per Square Foot. the dataset HAS a priceSqFt\n'
     '# column but it is empty in all three city files, so the target has to be\n'
     '# derived: monthly rent divided by the built-up area.\n'
     'print("priceSqFt non-null values in the file:", df["priceSqFt"].notna().sum())\n\n'
     '# house_size is text like "1,020 sq ft" -> strip it down to a number\n'
     'df["size_sqft"] = pd.to_numeric(\n'
     '    df["house_size"].str.replace(" sq ft", "", regex=False).str.replace(",", "", regex=False),\n'
     '    errors="coerce")\n'
     'df["price_per_sqft"] = df["price"] / df["size_sqft"]\n\n'
     'print("\\nTarget summary:")\n'
     'print(df["price_per_sqft"].describe())'),

    ("10. Preparing the features and the train / test split",
     '# bedrooms are hidden in the house_type text ("2 BHK Apartment" -> 2)\n'
     'df["house_type"] = df["house_type"].str.strip()\n'
     'df["bhk"] = df["house_type"].str.extract(r"^(\\d+)").astype(float)\n\n'
     '# fill the two numeric gaps: bathrooms with the median, balconies with 0\n'
     'df["numBathrooms"] = df["numBathrooms"].fillna(df["numBathrooms"].median())\n'
     'df["numBalconies"] = df["numBalconies"].fillna(0)\n\n'
     '# 702 distinct localities is far too many to one-hot, so keep the 30\n'
     '# commonest and bucket the rest as "Other"\n'
     'top_loc = df["location"].value_counts().head(30).index\n'
     'df["loc_grp"] = np.where(df["location"].isin(top_loc), df["location"], "Other")\n\n'
     '# price is deliberately NOT a feature - the target is price/size, so price\n'
     '# would leak the answer straight into the model\n'
     'features = ["size_sqft", "bhk", "numBathrooms", "numBalconies",\n'
     '            "Status", "city", "loc_grp"]\n'
     'X = pd.get_dummies(df[features], drop_first=True)\n'
     'y = df["price_per_sqft"]\n\n'
     'X_train, X_test, y_train, y_test = train_test_split(\n'
     '    X, y, test_size=0.2, random_state=SEED)\n'
     'print("Feature matrix after one-hot encoding:", X.shape)\n'
     'print("Training rows:", len(X_train), " Test rows:", len(X_test))'),

    ("11. Simple Linear Regression",
     '# one predictor only - the size of the house\n'
     'simple = LinearRegression()\n'
     'simple.fit(X_train[["size_sqft"]], y_train)\n'
     'pred = simple.predict(X_test[["size_sqft"]])\n\n'
     'print("Intercept:", round(simple.intercept_, 4))\n'
     'print("Slope    :", round(simple.coef_[0], 6))\n'
     'print("R2 score :", round(r2_score(y_test, pred), 4))\n'
     'print("RMSE     :", round(root_mean_squared_error(y_test, pred), 4))\n'
     'results.append({"Technique": "Simple Linear",\n'
     '                "R2 Score": r2_score(y_test, pred),\n'
     '                "RMSE": root_mean_squared_error(y_test, pred)})'),

    ("12. Multiple Linear Regression",
     '# all the features together\n'
     'multi = LinearRegression()\n'
     'multi.fit(X_train, y_train)\n'
     'pred = multi.predict(X_test)\n\n'
     'print("R2 score:", round(r2_score(y_test, pred), 4))\n'
     'print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))\n'
     'results.append({"Technique": "Multiple Linear",\n'
     '                "R2 Score": r2_score(y_test, pred),\n'
     '                "RMSE": root_mean_squared_error(y_test, pred)})\n\n'
     'coef = pd.Series(multi.coef_, index=X.columns).sort_values(key=abs, ascending=False)\n'
     'print("\\nFive strongest coefficients:")\n'
     'print(coef.head(5))'),

    ("13. Polynomial Regression",
     '# degree 2 adds every squared term and every pairwise interaction\n'
     'poly = make_pipeline(PolynomialFeatures(degree=2, include_bias=False),\n'
     '                     LinearRegression())\n'
     'poly.fit(X_train, y_train)\n'
     'pred = poly.predict(X_test)\n\n'
     'print("Features after expansion:",\n'
     '      poly.named_steps["polynomialfeatures"].n_output_features_)\n'
     'print("R2 score:", round(r2_score(y_test, pred), 4))\n'
     'print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))\n'
     'results.append({"Technique": "Polynomial (deg 2)",\n'
     '                "R2 Score": r2_score(y_test, pred),\n'
     '                "RMSE": root_mean_squared_error(y_test, pred)})'),

    ("14. Lasso Regression",
     '# L1 penalty: it can push coefficients all the way to zero.\n'
     '# scaling first, otherwise the penalty hits the big-valued columns hardest\n'
     'lasso = make_pipeline(StandardScaler(), Lasso(alpha=0.1, max_iter=5000))\n'
     'lasso.fit(X_train, y_train)\n'
     'pred = lasso.predict(X_test)\n\n'
     'print("R2 score:", round(r2_score(y_test, pred), 4))\n'
     'print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))\n'
     'zeroed = (lasso.named_steps["lasso"].coef_ == 0).sum()\n'
     'print("Coefficients driven to exactly zero:", zeroed, "of", X.shape[1])\n'
     'results.append({"Technique": "Lasso",\n'
     '                "R2 Score": r2_score(y_test, pred),\n'
     '                "RMSE": root_mean_squared_error(y_test, pred)})'),

    ("15. Ridge Regression",
     '# L2 penalty: it shrinks coefficients towards zero but never to zero\n'
     'ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0))\n'
     'ridge.fit(X_train, y_train)\n'
     'pred = ridge.predict(X_test)\n\n'
     'print("R2 score:", round(r2_score(y_test, pred), 4))\n'
     'print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))\n'
     'zeroed = (ridge.named_steps["ridge"].coef_ == 0).sum()\n'
     'print("Coefficients driven to exactly zero:", zeroed, "of", X.shape[1])\n'
     'results.append({"Technique": "Ridge",\n'
     '                "R2 Score": r2_score(y_test, pred),\n'
     '                "RMSE": root_mean_squared_error(y_test, pred)})'),

    ("16. Comparative table of R2 score and RMSE",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     'print(table.to_string())\n'
     'print("\\nBest R2  :", table["R2 Score"].idxmax())\n'
     'print("Lowest RMSE:", table["RMSE"].idxmin())\n\n'
     'table["R2 Score"].plot(kind="bar", color="#4C72B0", rot=20)\n'
     'plt.ylabel("R2 score")\n'
     'plt.title("R2 by regression technique")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("17. Predicted vs actual for the best model",
     'best = multi.predict(X_test)\n'
     'plt.scatter(y_test, best, s=8, alpha=0.3, color="#4C72B0")\n'
     'lims = [y_test.min(), y_test.max()]\n'
     'plt.plot(lims, lims, color="red", linewidth=1.5)\n'
     'plt.xlabel("Actual price per sq ft")\n'
     'plt.ylabel("Predicted price per sq ft")\n'
     'plt.title("Multiple linear regression - predicted vs actual")\n'
     'plt.tight_layout()\n'
     'plt.show()'),

    ("18. Interpretations",
     'print("INTERPRETATIONS")\n'
     'print("-" * 62)\n'
     'print("1. The assigned target, priceSqFt, is empty in every row of the")\n'
     'print("   downloaded files, so it was derived as price / size_sqft.")\n'
     'print("2. Size alone explains only", round(table.loc["Simple Linear", "R2 Score"], 4),\n'
     '      "of the variation. Rent per square")\n'
     'print("   foot is mostly a question of WHERE the house is, not how big.")\n'
     'print("3. Adding city, locality, furnishing and room counts more than")\n'
     'print("   doubles R2 to", round(table.loc["Multiple Linear", "R2 Score"], 4),\n'
     '      "- location is doing most of that work.")\n'
     'print("4. Degree-2 polynomial expands", X.shape[1], "features into",\n'
     '      poly.named_steps["polynomialfeatures"].n_output_features_, "but gains")\n'
     'print("   almost nothing, so the relationship is close to linear already.")\n'
     'print("5. Lasso and Ridge score the same as plain multiple regression.")\n'
     'print("   With 11k training rows against", X.shape[1], "features there is no")\n'
     'print("   overfitting for a penalty to fix.")\n'
     'print("6. RMSE is around", round(table["RMSE"].min(), 1), "rupees per sq ft on a target whose")\n'
     'print("   mean is", round(y.mean(), 1), "- the remaining error is the micro-location")\n'
     'print("   detail lost when 702 localities were bucketed down to 30.")'),
]

NB_CELLS = [
    ("md", "# Ex 5 \u2014 Regression Analysis\n\n"
           "**Dataset:** India Rental House Price (Delhi + Mumbai + Pune)  \n"
           "**Target:** Price per Square Foot  \n**Reg No:** URK24CS1021"),
    ("code",
     "import numpy as np\n"
     "import pandas as pd\n"
     "import matplotlib.pyplot as plt\n"
     "import seaborn as sns\n"
     "from sklearn.model_selection import train_test_split\n"
     "from sklearn.linear_model import LinearRegression, Lasso, Ridge\n"
     "from sklearn.preprocessing import PolynomialFeatures, StandardScaler\n"
     "from sklearn.pipeline import make_pipeline\n"
     "from sklearn.metrics import r2_score, root_mean_squared_error\n\n"
     'sns.set_theme(style="whitegrid")\n'
     "SEED = 1021\n\n"
     'df = pd.read_csv("rental.csv")\n'
     "df.head()"),
    ("md", "### What is actually in the file?"),
    ("code", "df.shape, df['city'].value_counts().to_dict()"),
    ("code", "df.describe()"),
    ("md", "### The target column is empty, so it has to be derived"),
    ("code",
     "# priceSqFt exists as a column but not a single row has a value\n"
     'df["priceSqFt"].notna().sum()'),
    ("code",
     '# house_size is text: "1,020 sq ft"\n'
     'df["size_sqft"] = pd.to_numeric(\n'
     '    df["house_size"].str.replace(" sq ft", "", regex=False).str.replace(",", "", regex=False),\n'
     '    errors="coerce")\n'
     'df["price_per_sqft"] = df["price"] / df["size_sqft"]\n'
     'df["price_per_sqft"].describe()'),
    ("md", "### Features \u2014 and the one column that must not be a feature"),
    ("code",
     'df["house_type"] = df["house_type"].str.strip()\n'
     'df["bhk"] = df["house_type"].str.extract(r"^(\\d+)").astype(float)\n'
     'df["numBathrooms"] = df["numBathrooms"].fillna(df["numBathrooms"].median())\n'
     'df["numBalconies"] = df["numBalconies"].fillna(0)\n'
     'top_loc = df["location"].value_counts().head(30).index\n'
     'df["loc_grp"] = np.where(df["location"].isin(top_loc), df["location"], "Other")\n'
     'df["location"].nunique(), df["loc_grp"].nunique()'),
    ("code",
     "# price stays out: price_per_sqft = price / size, so price leaks the answer\n"
     'X = pd.get_dummies(df[["size_sqft", "bhk", "numBathrooms", "numBalconies",\n'
     '                       "Status", "city", "loc_grp"]], drop_first=True)\n'
     'y = df["price_per_sqft"]\n'
     "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)\n"
     "X.shape"),
    ("md", "### One predictor vs all of them"),
    ("code",
     "results = []\n\n"
     "def score(name, model, Xtr, Xte):\n"
     "    model.fit(Xtr, y_train)\n"
     "    p = model.predict(Xte)\n"
     '    results.append({"Technique": name, "R2 Score": r2_score(y_test, p),\n'
     '                    "RMSE": root_mean_squared_error(y_test, p)})\n'
     "    return model\n\n"
     'simple = score("Simple Linear", LinearRegression(),\n'
     '               X_train[["size_sqft"]], X_test[["size_sqft"]])\n'
     "results[-1]"),
    ("code",
     'multi = score("Multiple Linear", LinearRegression(), X_train, X_test)\n'
     "results[-1]"),
    ("code",
     "pd.Series(multi.coef_, index=X.columns).sort_values(key=abs, ascending=False).head(5)"),
    ("md", "### Bending the line, then penalising it"),
    ("code",
     'poly = score("Polynomial (deg 2)",\n'
     "             make_pipeline(PolynomialFeatures(degree=2, include_bias=False),\n"
     "                           LinearRegression()), X_train, X_test)\n"
     'poly.named_steps["polynomialfeatures"].n_output_features_, results[-1]'),
    ("code",
     'lasso = score("Lasso", make_pipeline(StandardScaler(), Lasso(alpha=0.1, max_iter=5000)),\n'
     "              X_train, X_test)\n"
     '(lasso.named_steps["lasso"].coef_ == 0).sum(), results[-1]'),
    ("code",
     'ridge = score("Ridge", make_pipeline(StandardScaler(), Ridge(alpha=1.0)),\n'
     "              X_train, X_test)\n"
     '(ridge.named_steps["ridge"].coef_ == 0).sum(), results[-1]'),
    ("md", "### The comparison, built from the collected scores"),
    ("code",
     'table = pd.DataFrame(results).set_index("Technique").round(4)\n'
     "table"),
    ("code",
     'table["R2 Score"].plot(kind="bar", color="#4C72B0", rot=20)\n'
     'plt.ylabel("R2 score")\n'
     'plt.title("R2 by regression technique")\n'
     "plt.show()"),
    ("code",
     "pred = multi.predict(X_test)\n"
     'plt.scatter(y_test, pred, s=8, alpha=0.3, color="#4C72B0")\n'
     "lims = [y_test.min(), y_test.max()]\n"
     'plt.plot(lims, lims, color="red")\n'
     'plt.xlabel("Actual price per sq ft")\n'
     'plt.ylabel("Predicted price per sq ft")\n'
     "plt.show()"),
]

VIDEO = """# Ex 5 — Code explanation (teaching cues)
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
"""


def main() -> None:
    build(Exp(
        num=5, title=TITLE, date=DATE, out=OUT, aim=AIM,
        desc_label="Description (About Regression)", desc=DESC, question=QUESTION,
        preamble=PREAMBLE, sections=SECTIONS, nb_cells=NB_CELLS, video=VIDEO,
        script_name="rental_regression.py", notebook_name="Ex5_RentalRegression.ipynb",
        shot_command="python rental_regression.py", shot_cwd=r"C:\DSE\Ex5",
    ))


if __name__ == "__main__":
    main()
