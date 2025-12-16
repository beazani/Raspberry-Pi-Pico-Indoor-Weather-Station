import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load dataset
df = pd.read_csv("dataset_edge.csv")

bins = [0, 30, 45, 60, 120]
labels = [0, 1, 2, 3]

df["AgeClass"] = pd.cut(df["Age"], bins=bins, labels=labels, right=True)
df["AgeClass"] = df["AgeClass"].astype(int)
df.drop(columns=["Age"], inplace=True)


X = df[["AgeClass", "Sex", "Temperature"]].values
y = df["Comfort"].values  # 0 / 1

# Normalize features (IMPORTANT)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train / test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# Train logistic regression
model = LogisticRegression()
model.fit(X_train, y_train)

# Evaluate
y_prob = model.predict_proba(X_test)[:, 1]

# Apply custom threshold (60%)
threshold = 0.6
y_pred = (y_prob >= threshold).astype(int)
print("Accuracy:", accuracy_score(y_test, y_pred))

# Extract parameters
weights = model.coef_[0]
bias = model.intercept_[0]

print("\n=== MODEL PARAMETERS ===")
print("Weights:", weights)
print("Bias:", bias)
print("\n=== SCALER PARAMETERS ===")
print("Mean:", scaler.mean_)
print("Scale:", scaler.scale_)

# Let's assume 'Sex' is encoded as 0=female, 1=male
sex_encoded = 1  # male
age = 70
if age < 30:
    age_class = 0
elif age < 45:
    age_class = 1
elif age < 60:
    age_class = 2
else:
    age_class = 3

for temp in range(16, 35):
    # Create a single observation
    x_prova = np.array([[age_class, sex_encoded, temp]])
    
    # Scale the observation
    x_prova_scaled = scaler.transform(x_prova)
    
    # Predict
    prova = model.predict_proba(x_prova_scaled)[0][1]
    print(prova)
    if prova >= 0.63:
        output = 1
    else:
        output = 0
    print(f"Temperature={temp} => Comfort={output}")
