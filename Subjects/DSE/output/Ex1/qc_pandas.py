# Ex 1 - Manufacturing Quality Control (Pandas)
# URK24CS1021
import pandas as pd

# 1. convert a list of products to a Series
products = ["Widget A", "Widget B", "Gadget"]
product_series = pd.Series(products)
print("Products Series:")
print(product_series)

# 2. convert a dictionary to a DataFrame
data = {"Product": ["Tool X", "Tool Y"], "Tolerance": [0.1, 0.2]}
df = pd.DataFrame(data)
print("\nProducts DataFrame:")
print(df)
