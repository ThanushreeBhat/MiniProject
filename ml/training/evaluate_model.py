
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
)

from backend.config import RISK_OUTPUT_FILE

from ml.training.train_model import (
    FEATURES,
    TARGET,
    build_model,
    load_training_data,
)


# Output directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "ml" / "visualizations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_plot(filename):
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / filename,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()
    print("Saved:", filename)


def evaluate_model():

    print("\nRAILBLOCK MODEL EVALUATION")
    print("=" * 50)

    df, X, y = load_training_data()

    # ------------------------------------------------
    # 1. Training class distribution
    # ------------------------------------------------

    plt.figure(figsize=(7, 5))

    counts = y.value_counts().sort_index()

    plt.bar(
        ["No Failure", "Failure"],
        [counts.get(0, 0), counts.get(1, 0)]
    )

    plt.title("Training Dataset Class Distribution")
    plt.xlabel("Failure Status")
    plt.ylabel("Number of Samples")

    save_plot("class_distribution.png")

    # ------------------------------------------------
    # 2. Chronological train-test split
    # ------------------------------------------------

    if "snapshot_date" not in df.columns:
        raise ValueError(
            "snapshot_date is missing. "
            "Cannot perform chronological evaluation."
        )

    dates = pd.to_datetime(
        df["snapshot_date"],
        errors="coerce"
    )

    latest_date = dates.max()

    if pd.isna(latest_date):
        raise ValueError("No valid snapshot dates found.")

    train_mask = dates < latest_date
    test_mask = dates == latest_date

    if not train_mask.any() or not test_mask.any():
        raise ValueError(
            "Unable to create chronological train-test split."
        )

    X_train = df.loc[train_mask, FEATURES]
    X_test = df.loc[test_mask, FEATURES]

    y_train = df.loc[train_mask, TARGET].astype(int)
    y_test = df.loc[test_mask, TARGET].astype(int)

    if y_train.nunique() < 2:
        raise ValueError(
            "Training split does not contain both classes."
        )

    print("\nTRAINING SAMPLES:", len(X_train))
    print("TESTING SAMPLES:", len(X_test))
    print("TEST SNAPSHOT:", latest_date)

    # ------------------------------------------------
    # 3. Train evaluation model
    # ------------------------------------------------

    model = build_model()

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)

    positive_index = list(model.classes_).index(1)

    positive_probabilities = probabilities[:, positive_index]

    # ------------------------------------------------
    # 4. Classification metrics
    # ------------------------------------------------

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test, predictions, zero_division=0
    )

    recall = recall_score(
        y_test, predictions, zero_division=0
    )

    f1 = f1_score(
        y_test, predictions, zero_division=0
    )

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }

    print("\nCLASSIFICATION REPORT")
    print(
        classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=["No Failure", "Failure"],
            zero_division=0
        )
    )

    # ------------------------------------------------
    # 5. Confusion matrix
    # ------------------------------------------------

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1]
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["No Failure", "Failure"]
    )

    fig, ax = plt.subplots(figsize=(7, 6))

    display.plot(
        ax=ax,
        cmap="Blues",
        values_format="d"
    )

    plt.title("Random Forest Confusion Matrix")

    save_plot("confusion_matrix.png")

    # ------------------------------------------------
    # 6. ROC curve
    # ------------------------------------------------

    if y_test.nunique() == 2:

        roc_auc = roc_auc_score(
            y_test,
            positive_probabilities
        )

        metrics["roc_auc"] = roc_auc

        fpr, tpr, _ = roc_curve(
            y_test,
            positive_probabilities
        )

        plt.figure(figsize=(7, 5))

        plt.plot(
            fpr,
            tpr,
            label=f"Random Forest (AUC = {roc_auc:.3f})"
        )

        plt.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
            label="Random Classifier"
        )

        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend()

        save_plot("roc_curve.png")

    else:
        print("\nROC-AUC unavailable: test set has only one class.")

    # ------------------------------------------------
    # 7. Precision-Recall curve
    # ------------------------------------------------

    if (y_test == 1).sum() > 0:

        ap = average_precision_score(
            y_test,
            positive_probabilities
        )

        metrics["average_precision"] = ap

        precision_values, recall_values, _ = (
            precision_recall_curve(
                y_test,
                positive_probabilities
            )
        )

        plt.figure(figsize=(7, 5))

        plt.plot(
            recall_values,
            precision_values,
            label=f"Average Precision = {ap:.3f}"
        )

        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision-Recall Curve")
        plt.legend()

        save_plot("precision_recall_curve.png")

    else:
        print(
            "\nPR-AUC unavailable: test set has no positive samples."
        )

    # ------------------------------------------------
    # 8. Feature importance
    # ------------------------------------------------

    preprocessing = model.named_steps["preprocessing"]

    classifier = model.named_steps["model"]

    feature_names = preprocessing.get_feature_names_out()

    importance = pd.DataFrame({
        "feature": feature_names,
        "importance": classifier.feature_importances_
    })

    importance = importance.sort_values(
        "importance",
        ascending=False
    )

    importance.to_csv(
        OUTPUT_DIR / "feature_importance.csv",
        index=False
    )

    top_features = importance.head(20).sort_values(
        "importance"
    )

    plt.figure(figsize=(10, 8))

    plt.barh(
        top_features["feature"],
        top_features["importance"]
    )

    plt.xlabel("Importance")
    plt.ylabel("Features")
    plt.title("Top 20 Random Forest Feature Importances")

    save_plot("feature_importance.png")

    # ------------------------------------------------
    # 9. Asset risk-level distribution
    # ------------------------------------------------

    if not RISK_OUTPUT_FILE.exists():
        print(
            "\nRisk prediction file not found. "
            "Skipping asset risk visualizations."
        )

    else:

        risk_df = pd.read_csv(RISK_OUTPUT_FILE)

        if "risk_level" in risk_df.columns:

            risk_order = [
                "Low", "Medium", "High", "Critical"
            ]

            risk_counts = (
                risk_df["risk_level"]
                .value_counts()
                .reindex(risk_order, fill_value=0)
            )

            plt.figure(figsize=(8, 5))

            plt.bar(
                risk_counts.index,
                risk_counts.values
            )

            plt.xlabel("Risk Level")
            plt.ylabel("Number of Assets")
            plt.title("Predicted Asset Risk Distribution")

            save_plot("risk_distribution.png")

        # --------------------------------------------
        # 10. Predicted failure probability histogram
        # --------------------------------------------

        probability_column = (
            "predicted_failure_probability"
        )

        if probability_column in risk_df.columns:

            plt.figure(figsize=(8, 5))

            plt.hist(
                risk_df[probability_column].dropna(),
                bins=15,
                edgecolor="black"
            )

            plt.xlabel("Predicted Failure Probability")
            plt.ylabel("Number of Assets")
            plt.title("Asset Failure Probability Distribution")

            save_plot("risk_probability_distribution.png")

    # ------------------------------------------------
    # 11. Save evaluation metrics
    # ------------------------------------------------

    metrics_df = pd.DataFrame(
        list(metrics.items()),
        columns=["Metric", "Value"]
    )

    metrics_df.to_csv(
        OUTPUT_DIR / "evaluation_metrics.csv",
        index=False
    )

    print("\nEVALUATION METRICS")
    print(metrics_df.to_string(index=False))

    print("\nALL AVAILABLE GRAPHS GENERATED")
    print("Output folder:", OUTPUT_DIR)


if __name__ == "__main__":
    evaluate_model()
