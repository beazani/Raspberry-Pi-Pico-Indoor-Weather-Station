import pandas as pd

df = pd.read_csv("ashrae_db2.01.csv", low_memory=False)

# Keep only needed columns
columns_to_keep = ["Age", "Sex", "Air temperature (C)", "Thermal comfort"]
df = df[columns_to_keep]

# Rename columns
df = df.rename(columns={
    "Air temperature (C)": "Temperature",
    "Thermal comfort": "Comfort"
})

# Drop remaining missing values
df.dropna(inplace=True)

df["Age"] = df["Age"].astype(int)

# Convert Sex to numeric
df["Sex"] = df["Sex"].map({"Male": 1, "Female": 0})

# Replace non-numeric entries with NaN
df["Comfort"] = pd.to_numeric(df["Comfort"], errors="coerce")

# Drop rows where Comfort could not be converted
df = df.dropna(subset=["Comfort"])

df["Comfort"] = df["Comfort"].astype(int)
# Keep only rows where Comfort is NOT 5
#df = df[df["Comfort"] != 5]
df["Comfort"] = (df["Comfort"] >= 5).astype(int)

counts = df["Comfort"].value_counts()
print(counts)

# Add timestamp column (needed for Edge Impulse)
#df.insert(0, "timestamp", range(0, len(df)*100, 100))

# Save final CSV
df.to_csv("dataset_edge.csv", index=False)
