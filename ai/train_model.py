import os
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

# Ensure ai directory exists
os.makedirs("ai", exist_ok=True)

# Normal data
normal = np.random.normal(
    loc=[5, 200, 300, 0, 0],
    scale=[2, 100, 100, 0.05, 0.05],
    size=(500, 5)
)

# Anomalies
anomalies = np.random.normal(
    loc=[0.5, 10, 20000, 1, 1],
    scale=[0.5, 10, 1000, 0, 0],
    size=(50, 5)
)

X = np.vstack([normal, anomalies])

model = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=42
)

model.fit(X)

joblib.dump(model, os.path.join("ai", "isolation_forest.pkl"))

print("✅ Model trained and saved")
