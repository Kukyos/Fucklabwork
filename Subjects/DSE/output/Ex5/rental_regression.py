# Ex 5 - Regression Analysis
# URK24CS1021

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Lasso, Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, root_mean_squared_error

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (7, 4.5)
pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 20)

SEED = 1021  # my reg no, so every run splits the same way
results = []  # every model appends its scores here for the final table

# 1. Import the dataset
# the kaggle download ships one csv per city; they share a schema, so I
# concatenated Delhi + Mumbai + Pune into one file before loading
df = pd.read_csv("rental.csv")
print("Rows loaded:", len(df))
print(df[["house_type", "house_size", "location", "city", "price"]].head())

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

# 6. Shape of the dataset
print("Shape (rows, columns):", df.shape)
print("Rows   :", df.shape[0])
print("Columns:", df.shape[1])
print("\nRows per city:")
print(df["city"].value_counts())

# 7. Statistical inferences
print(df.describe())
print("\nMissing values per column:")
print(df.isnull().sum())

# 8. Data types
print(df.dtypes)
print("\nNumeric columns    :", list(df.select_dtypes(include="number").columns))
print("Categorical columns:", list(df.select_dtypes(include="object").columns))

# 9. Building the target column 'Price per Square Foot'
# the assigned target is Price per Square Foot. the dataset HAS a priceSqFt
# column but it is empty in all three city files, so the target has to be
# derived: monthly rent divided by the built-up area.
print("priceSqFt non-null values in the file:", df["priceSqFt"].notna().sum())

# house_size is text like "1,020 sq ft" -> strip it down to a number
df["size_sqft"] = pd.to_numeric(
    df["house_size"].str.replace(" sq ft", "", regex=False).str.replace(",", "", regex=False),
    errors="coerce")
df["price_per_sqft"] = df["price"] / df["size_sqft"]

print("\nTarget summary:")
print(df["price_per_sqft"].describe())

# 10. Preparing the features and the train / test split
# bedrooms are hidden in the house_type text ("2 BHK Apartment" -> 2)
df["house_type"] = df["house_type"].str.strip()
df["bhk"] = df["house_type"].str.extract(r"^(\d+)").astype(float)

# fill the two numeric gaps: bathrooms with the median, balconies with 0
df["numBathrooms"] = df["numBathrooms"].fillna(df["numBathrooms"].median())
df["numBalconies"] = df["numBalconies"].fillna(0)

# 702 distinct localities is far too many to one-hot, so keep the 30
# commonest and bucket the rest as "Other"
top_loc = df["location"].value_counts().head(30).index
df["loc_grp"] = np.where(df["location"].isin(top_loc), df["location"], "Other")

# price is deliberately NOT a feature - the target is price/size, so price
# would leak the answer straight into the model
features = ["size_sqft", "bhk", "numBathrooms", "numBalconies",
            "Status", "city", "loc_grp"]
X = pd.get_dummies(df[features], drop_first=True)
y = df["price_per_sqft"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED)
print("Feature matrix after one-hot encoding:", X.shape)
print("Training rows:", len(X_train), " Test rows:", len(X_test))

# 11. Simple Linear Regression
# one predictor only - the size of the house
simple = LinearRegression()
simple.fit(X_train[["size_sqft"]], y_train)
pred = simple.predict(X_test[["size_sqft"]])

print("Intercept:", round(simple.intercept_, 4))
print("Slope    :", round(simple.coef_[0], 6))
print("R2 score :", round(r2_score(y_test, pred), 4))
print("RMSE     :", round(root_mean_squared_error(y_test, pred), 4))
results.append({"Technique": "Simple Linear",
                "R2 Score": r2_score(y_test, pred),
                "RMSE": root_mean_squared_error(y_test, pred)})

# 12. Multiple Linear Regression
# all the features together
multi = LinearRegression()
multi.fit(X_train, y_train)
pred = multi.predict(X_test)

print("R2 score:", round(r2_score(y_test, pred), 4))
print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))
results.append({"Technique": "Multiple Linear",
                "R2 Score": r2_score(y_test, pred),
                "RMSE": root_mean_squared_error(y_test, pred)})

coef = pd.Series(multi.coef_, index=X.columns).sort_values(key=abs, ascending=False)
print("\nFive strongest coefficients:")
print(coef.head(5))

# 13. Polynomial Regression
# degree 2 adds every squared term and every pairwise interaction
poly = make_pipeline(PolynomialFeatures(degree=2, include_bias=False),
                     LinearRegression())
poly.fit(X_train, y_train)
pred = poly.predict(X_test)

print("Features after expansion:",
      poly.named_steps["polynomialfeatures"].n_output_features_)
print("R2 score:", round(r2_score(y_test, pred), 4))
print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))
results.append({"Technique": "Polynomial (deg 2)",
                "R2 Score": r2_score(y_test, pred),
                "RMSE": root_mean_squared_error(y_test, pred)})

# 14. Lasso Regression
# L1 penalty: it can push coefficients all the way to zero.
# scaling first, otherwise the penalty hits the big-valued columns hardest
lasso = make_pipeline(StandardScaler(), Lasso(alpha=0.1, max_iter=5000))
lasso.fit(X_train, y_train)
pred = lasso.predict(X_test)

print("R2 score:", round(r2_score(y_test, pred), 4))
print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))
zeroed = (lasso.named_steps["lasso"].coef_ == 0).sum()
print("Coefficients driven to exactly zero:", zeroed, "of", X.shape[1])
results.append({"Technique": "Lasso",
                "R2 Score": r2_score(y_test, pred),
                "RMSE": root_mean_squared_error(y_test, pred)})

# 15. Ridge Regression
# L2 penalty: it shrinks coefficients towards zero but never to zero
ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
ridge.fit(X_train, y_train)
pred = ridge.predict(X_test)

print("R2 score:", round(r2_score(y_test, pred), 4))
print("RMSE    :", round(root_mean_squared_error(y_test, pred), 4))
zeroed = (ridge.named_steps["ridge"].coef_ == 0).sum()
print("Coefficients driven to exactly zero:", zeroed, "of", X.shape[1])
results.append({"Technique": "Ridge",
                "R2 Score": r2_score(y_test, pred),
                "RMSE": root_mean_squared_error(y_test, pred)})

# 16. Comparative table of R2 score and RMSE
table = pd.DataFrame(results).set_index("Technique").round(4)
print(table.to_string())
print("\nBest R2  :", table["R2 Score"].idxmax())
print("Lowest RMSE:", table["RMSE"].idxmin())

table["R2 Score"].plot(kind="bar", color="#4C72B0", rot=20)
plt.ylabel("R2 score")
plt.title("R2 by regression technique")
plt.tight_layout()
plt.show()

# 17. Predicted vs actual for the multiple linear model
# polynomial edges it on R2 by 0.0003, which is noise - so the plot uses
# the plain multiple linear model, the simplest of the ones that tied
best = multi.predict(X_test)
plt.scatter(y_test, best, s=8, alpha=0.3, color="#4C72B0")
lims = [y_test.min(), y_test.max()]
plt.plot(lims, lims, color="red", linewidth=1.5)
plt.xlabel("Actual price per sq ft")
plt.ylabel("Predicted price per sq ft")
plt.title("Multiple linear regression - predicted vs actual")
plt.tight_layout()
plt.show()

# 18. Interpretations
print("INTERPRETATIONS")
print("-" * 62)
print("1. The assigned target, priceSqFt, is empty in every row of the")
print("   downloaded files, so it was derived as price / size_sqft.")
print("2. Size alone explains only", round(table.loc["Simple Linear", "R2 Score"], 4),
      "of the variation. Rent per square")
print("   foot is mostly a question of WHERE the house is, not how big.")
print("3. Adding city, locality, furnishing and room counts more than")
print("   doubles R2 to", round(table.loc["Multiple Linear", "R2 Score"], 4),
      "- location is doing most of that work.")
print("4. Degree-2 polynomial expands", X.shape[1], "features into",
      poly.named_steps["polynomialfeatures"].n_output_features_, "but gains")
print("   almost nothing, so the relationship is close to linear already.")
print("5. Lasso and Ridge score the same as plain multiple regression.")
print("   With 11k training rows against", X.shape[1], "features there is no")
print("   overfitting for a penalty to fix.")
print("6. RMSE is around", round(table["RMSE"].min(), 1), "rupees per sq ft on a target whose")
print("   mean is", round(y.mean(), 1), "- the remaining error is the micro-location")
print("   detail lost when 702 localities were bucketed down to 30.")