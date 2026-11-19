
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
)

from backend.config import (
    RISK_TRAINING_FILE,
    MODEL_FILE,
    create_directories,
)


TARGET = "failure_in_next_90d"

# Only use features that exist in BOTH training and
# current asset prediction datasets.
FEATURES = [
    "department",
    "asset_type",
    "section_id",
    "criticality",
    "installation_year",
    "age_years",
    "days_since_last_maintenance",
    "has_maintenance_history",
    "maintenance_count_90d",
    "maintenance_count_180d",
    "maintenance_count_365d",
    "defect_count_90d",
    "defect_count_180d",
    "defect_count_365d",
    "failure_count_180d",
    "failure_count_365d",
    "average_downtime_min_180d",
    "average_severity_score_180d",
    "average_downtime_min_365d",
    "total_downtime_min_365d",
    "maintenance_frequency_90d",
    "failure_rate_365d",
    "defect_rate_365d",
]


CATEGORICAL_FEATURES = [
    "department",
    "asset_type",
    "section_id",
    "criticality",
]

NUMERICAL_FEATURES = [
    feature
    for feature in FEATURES
    if feature not in CATEGORICAL_FEATURES
]


def load_training_data():

    if not RISK_TRAINING_FILE.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {RISK_TRAINING_FILE}"
        )

    df = pd.read_csv(RISK_TRAINING_FILE)

    required = set(FEATURES + [TARGET])

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing training columns: {sorted(missing)}"
        )

    df = df.dropna(subset=[TARGET]).copy()

    X = df[FEATURES].copy()
    y = pd.to_numeric(df[TARGET], errors="raise").astype(int)

    if not set(y.unique()).issubset({0, 1}):
        raise ValueError("Target must contain only 0 and 1.")

    if y.nunique() != 2:
        raise ValueError(
            "Training data must contain both target classes."
        )

    return df, X, y


def build_model():

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore")
        ),
    ])

    preprocessing = ColumnTransformer([
        (
            "numeric",
            numeric_pipeline,
            NUMERICAL_FEATURES
        ),
        (
            "categorical",
            categorical_pipeline,
            CATEGORICAL_FEATURES
        ),
    ])

    classifier = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline([
        ("preprocessing", preprocessing),
        ("model", classifier),
    ])


def temporal_evaluation(df):

    """
    Evaluate using the latest snapshot as the test set.
    This keeps the evaluation chronological.
    """

    if "snapshot_date" not in df.columns:
        print(
            "No snapshot_date available. "
            "Skipping temporal evaluation."
        )
        return

    dates = pd.to_datetime(
        df["snapshot_date"],
        errors="coerce"
    )

    valid_dates = dates.dropna().unique()

    if len(valid_dates) < 2:
        print("Not enough dates for temporal evaluation.")
        return

    latest_date = dates.max()

    train_mask = dates < latest_date
    test_mask = dates == latest_date

    if not train_mask.any() or not test_mask.any():
        print("Unable to create temporal split.")
        return

    X_train = df.loc[train_mask, FEATURES]
    y_train = df.loc[train_mask, TARGET].astype(int)

    X_test = df.loc[test_mask, FEATURES]
    y_test = df.loc[test_mask, TARGET].astype(int)

    if y_train.nunique() < 2 or y_test.nunique() < 2:
        print(
            "Temporal split does not contain both classes "
            "in training and testing. Skipping metrics."
        )
        return

    evaluation_model = build_model()

    evaluation_model.fit(X_train, y_train)

    predictions = evaluation_model.predict(X_test)

    probabilities = evaluation_model.predict_proba(X_test)

    positive_index = list(
        evaluation_model.classes_
    ).index(1)

    positive_probabilities = probabilities[:, positive_index]

    print("\nTEMPORAL EVALUATION")
    print("=" * 45)

    print("Training rows:", len(X_train))
    print("Testing rows:", len(X_test))
    print("Test snapshot:", latest_date)

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))

    print(
        "ROC-AUC:",
        round(
            roc_auc_score(y_test, positive_probabilities),
            4
        )
    )

    print(
        "PR-AUC:",
        round(
            average_precision_score(
                y_test,
                positive_probabilities
            ),
            4
        )
    )


def train_final_model(X, y):

    print("\nTRAINING FINAL RANDOM FOREST")
    print("=" * 45)

    model = build_model()

    model.fit(X, y)

    # Save trained model
    create_directories()

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(model, MODEL_FILE)

    print("\nMODEL SAVED SUCCESSFULLY")
    print("Path:", MODEL_FILE)
    print("Size:", MODEL_FILE.stat().st_size, "bytes")

    return model


def main():

    print("RAILBLOCK RANDOM FOREST TRAINING")
    print("=" * 45)

    df, X, y = load_training_data()

    print("Training rows:", len(df))
    print("Features:", len(FEATURES))
    print("Target distribution:")
    print(y.value_counts().to_string())

    print("\nFeatures used:")
    for feature in FEATURES:
        print("-", feature)

    # Evaluate on the latest chronological snapshot
    temporal_evaluation(df)

    # Refit using all available training data
    model = train_final_model(X, y)

    print("\nFINAL MODEL INFORMATION")
    print("Model:", type(model.named_steps["model"]).__name__)
    print("Features:", len(model.feature_names_in_))
    print("Classes:", model.classes_)

    print("\nTRAINING COMPLETED")


if __name__ == "__main__":
    main()
