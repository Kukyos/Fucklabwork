# Ex 2 - Working with Pandas (fanspeed.csv)
# URK24CS1021

import pandas as pd

pd.set_option("display.max_rows", 15)
pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 10)

# 1. Import the dataset
df = pd.read_csv("fanspeed.csv")
print(df)

# 2. Display the first 10 rows and last 8 rows
print("First 10 rows:")
print(df.head(10))

print("\nLast 8 rows:")
print(df.tail(8))

# 3. Display information about the dataset
print("Column names:", list(df.columns))
print("\nShape:", df.shape)
print("\nStatistical inferences:")
print(df.describe())
print("\nData types:")
print(df.dtypes)
print("\nInfo:")
df.info()

# 4. Null values: examine, display, impute
# fanspeed.csv has no missing values as downloaded, so plant a few on a
# copy (fixed rows, reproducible) just to show detection + imputation
# -- the real df used from here on stays untouched
demo = df.copy()
demo.loc[[3, 27, 61], "Observed Fan Speed"] = None
print("Null values per column:")
print(demo.isnull().sum())

mean_speed = demo["Observed Fan Speed"].mean()
demo["Observed Fan Speed"] = demo["Observed Fan Speed"].fillna(mean_speed)
print("\nAfter imputing with the column mean:")
print(demo.isnull().sum())

# 5. Slicing the dataset
print("Single column:")
print(df["Temperature"].head())

print("\nMultiple columns:")
print(df[["Temperature", "Observed Fan Speed"]].head())

print("\nSingle row (loc):")
print(df.loc[5])

print("\nMultiple rows (loc):")
print(df.loc[5:8])

print("\nSingle row (iloc):")
print(df.iloc[5])

print("\nMultiple rows (iloc):")
print(df.iloc[5:8])

print("\nloc - rows + one column:")
print(df.loc[5:8, "Temperature"])

print("\niloc - rows + one column:")
print(df.iloc[5:8, 0])

print("\nConditional slicing (Temperature > 25):")
print(df[df["Temperature"] > 25].head())

# 6. Add a column to the end
# normal arithmetic operation
df["Speed_Per_Degree"] = df["Observed Fan Speed"] / df["Temperature"]
# apply() with a custom function
df["Speed_Level"] = df["Observed Fan Speed"].apply(lambda x: "High" if x > 60 else "Low")
# apply() with an inbuilt function
df["Speed_Rounded"] = df["Observed Fan Speed"].apply(round)
print(df.head())

# 7. Add a row and delete it
new_row = pd.DataFrame([{"Temperature": 40, "Observed Fan Speed": 120,
                          "Speed_Per_Degree": 3.0, "Speed_Level": "High",
                          "Speed_Rounded": 120}])
df = pd.concat([df, new_row], ignore_index=True)
print("After adding a row:")
print(df.tail(3))

df = df.drop(df.index[-1])
print("\nAfter deleting it:")
print(df.tail(3))

# 8. Sort ascending and descending
print("Ascending by Observed Fan Speed:")
print(df.sort_values("Observed Fan Speed").head())

print("\nDescending by Observed Fan Speed:")
print(df.sort_values("Observed Fan Speed", ascending=False).head())

# 9. Group by single and multiple conditions
print("Group by Speed_Level (single condition):")
print(df.groupby("Speed_Level")["Observed Fan Speed"].mean())

df["Temp_Band"] = df["Temperature"].apply(
    lambda t: "Low" if t < 15 else ("Mid" if t < 25 else "High"))
print("\nGroup by Speed_Level & Temp_Band (multiple conditions):")
print(df.groupby(["Speed_Level", "Temp_Band"])["Observed Fan Speed"].mean())

# 10. Pivot table
print(pd.pivot_table(df, index="Temp_Band", columns="Speed_Level",
                      values="Observed Fan Speed", aggfunc="mean"))

# 11. Ranking column, all methods
df["Rank_average"] = df["Observed Fan Speed"].rank(method="average")
df["Rank_min"] = df["Observed Fan Speed"].rank(method="min")
df["Rank_max"] = df["Observed Fan Speed"].rank(method="max")
df["Rank_first"] = df["Observed Fan Speed"].rank(method="first")
df["Rank_dense"] = df["Observed Fan Speed"].rank(method="dense")
print(df[["Observed Fan Speed", "Rank_average", "Rank_min",
          "Rank_max", "Rank_first", "Rank_dense"]].head())