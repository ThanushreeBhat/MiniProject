
from pathlib import Path

# Root directory of the RailBlock project
BASE_DIR = Path(__file__).resolve().parents[1]

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# ML directories
ML_DIR = BASE_DIR / "ml"
MODEL_DIR = ML_DIR / "models"
PREDICTION_DIR = ML_DIR / "outputs"

MODEL_FILE = MODEL_DIR / "risk_random_forest.joblib"

# Optimization and explanation
OPTIMIZATION_DIR = BASE_DIR / "optimization"
EXPLANATION_DIR = BASE_DIR / "explanation"

# Backend
BACKEND_DIR = BASE_DIR / "backend"

# Output directory
OUTPUT_DIR = BASE_DIR / "outputs"

# Input files
TASK_FILE = RAW_DATA_DIR / "maintenance_tasks.csv"
BLOCK_FILE = RAW_DATA_DIR / "block_availability.csv"
TRAIN_FILE = RAW_DATA_DIR / "train_movements.csv"

# ML feature files
ASSET_FEATURE_FILE = SYNTHETIC_DATA_DIR / "asset_features.csv"
ASSET_MASTER_FILE = SYNTHETIC_DATA_DIR / "asset_master.csv"
MAINTENANCE_HISTORY_FILE = (
    SYNTHETIC_DATA_DIR / "maintenance_history.csv"
)
RISK_TRAINING_FILE = (
    SYNTHETIC_DATA_DIR / "risk_training_dataset.csv"
)

# Main output files
RISK_OUTPUT_FILE = OUTPUT_DIR / "risk_predictions.csv"
CANDIDATE_OUTPUT_FILE = OUTPUT_DIR / "candidate_assignments.csv"
SCHEDULE_OUTPUT_FILE = OUTPUT_DIR / "optimized_schedule.csv"
UNSCHEDULED_OUTPUT_FILE = OUTPUT_DIR / "unscheduled_tasks.csv"
EXPLANATION_OUTPUT_FILE = OUTPUT_DIR / "task_explanations.csv"
VALIDATION_OUTPUT_FILE = OUTPUT_DIR / "validation_report.json"


def create_directories():
    """Create output directories if they do not exist."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
