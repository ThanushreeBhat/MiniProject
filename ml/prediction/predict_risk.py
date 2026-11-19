
import joblib
import pandas as pd

from backend.config import (
    MODEL_FILE,
    ASSET_FEATURE_FILE,
    RISK_OUTPUT_FILE,
    create_directories,
)


def classify_risk(probability):

    if probability >= 0.75:
        return "Critical"

    elif probability >= 0.50:
        return "High"

    elif probability >= 0.25:
        return "Medium"

    return "Low"


def predict_risk():

    print("\nRAILBLOCK ASSET RISK PREDICTION")
    print("=" * 45)

    # Check files
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_FILE}"
        )

    if not ASSET_FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Asset features not found: {ASSET_FEATURE_FILE}"
        )

    # Load trained model
    model = joblib.load(MODEL_FILE)

    # Load current asset features
    assets = pd.read_csv(ASSET_FEATURE_FILE)

    if "asset_id" not in assets.columns:
        raise ValueError(
            "asset_features.csv must contain asset_id."
        )

    # Get exact model input features
    model_features = list(model.feature_names_in_)

    missing = set(model_features) - set(assets.columns)

    if missing:
        raise ValueError(
            "Missing model features in asset_features.csv: "
            + str(sorted(missing))
        )

    # Preserve asset IDs separately
    asset_ids = assets["asset_id"].copy()

    X = assets[model_features].copy()

    # Predict probabilities
    probabilities = model.predict_proba(X)

    # Find probability column corresponding to class 1
    classes = list(model.classes_)

    if 1 not in classes:
        raise ValueError(
            "Model does not contain positive class 1."
        )

    positive_index = classes.index(1)

    failure_probabilities = probabilities[:, positive_index]

    # Create output
    results = pd.DataFrame({

        "asset_id": asset_ids,

        "predicted_failure_probability": (
            failure_probabilities
        ),

    })

    results["risk_level"] = (
        results["predicted_failure_probability"]
        .apply(classify_risk)
    )

    # Keep probabilities within valid range
    results["predicted_failure_probability"] = (
        results["predicted_failure_probability"]
        .clip(0, 1)
    )

    # Save predictions
    create_directories()

    RISK_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    results.to_csv(
        RISK_OUTPUT_FILE,
        index=False
    )

    # Display summary
    print("\nPREDICTION COMPLETED")
    print("-" * 45)

    print("Total assets:", len(results))

    print("\nRisk distribution:")
    print(
        results["risk_level"]
        .value_counts()
        .to_string()
    )

    print("\nHighest-risk assets:")

    print(
        results.sort_values(
            "predicted_failure_probability",
            ascending=False
        ).head(10).to_string(index=False)
    )

    print("\nOutput saved to:")
    print(RISK_OUTPUT_FILE)

    return results


if __name__ == "__main__":
    predict_risk()
