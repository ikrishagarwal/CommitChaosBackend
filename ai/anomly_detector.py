import joblib
import os

MODEL_PATH = os.path.join("ai", "isolation_forest.pkl")
model = joblib.load(MODEL_PATH)

def detect_anomaly(features):
    pred = model.predict([features])[0]
    score = model.decision_function([features])[0]

    return {
        "is_anomaly": pred == -1,
        "confidence": round(abs(score), 2)
    }
