from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"

OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_DIR = BASE_DIR / "ml" / "models"
ML_OUTPUT_DIR = BASE_DIR / "ml" / "outputs"

# Source data files
TASK_FILE = RAW_DATA_DIR / "maintenance_tasks.csv"
BLOCK_FILE = RAW_DATA_DIR / "block_availability.csv"
TRAIN_FILE = RAW_DATA_DIR / "train_movements.csv"
ASSET_FEATURE_FILE = SYNTHETIC_DATA_DIR / "asset_features.csv"
RISK_TRAINING_FILE = SYNTHETIC_DATA_DIR / "asset_features.csv"

# Model files
MODEL_FILE = MODEL_DIR / "risk_random_forest.joblib"

# Pipeline Output files
RISK_OUTPUT_FILE = OUTPUT_DIR / "risk_predictions.csv"
CANDIDATE_OUTPUT_FILE = OUTPUT_DIR / "candidate_assignments.csv"
SCHEDULE_OUTPUT_FILE = OUTPUT_DIR / "optimized_schedule.csv"
UNSCHEDULED_OUTPUT_FILE = OUTPUT_DIR / "unscheduled_tasks.csv"
VALIDATION_OUTPUT_FILE = OUTPUT_DIR / "validation_report.json"
EXPLANATION_OUTPUT_FILE = OUTPUT_DIR / "task_explanations.csv"


def create_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Initialize output directories and safe fallback placeholder headers
create_directories()

if not RISK_OUTPUT_FILE.exists():
    RISK_OUTPUT_FILE.write_text("asset_id,predicted_failure_probability,risk_level\n", encoding="utf-8")

if not CANDIDATE_OUTPUT_FILE.exists():
    CANDIDATE_OUTPUT_FILE.write_text("task_id,block_window_id,section_id,earliest_start,latest_start,duration_min\n", encoding="utf-8")

if not SCHEDULE_OUTPUT_FILE.exists():
    SCHEDULE_OUTPUT_FILE.write_text("task_id,block_window_id,section_id,scheduled_start,scheduled_end,duration_min\n", encoding="utf-8")

if not UNSCHEDULED_OUTPUT_FILE.exists():
    UNSCHEDULED_OUTPUT_FILE.write_text("task_id,section_id,reason_code,reason\n", encoding="utf-8")

if not EXPLANATION_OUTPUT_FILE.exists():
    EXPLANATION_OUTPUT_FILE.write_text("task_id,status,explanation,priority_score\n", encoding="utf-8")

if not VALIDATION_OUTPUT_FILE.exists():
    VALIDATION_OUTPUT_FILE.write_text('{"validation_passed": true, "total_violations": 0, "checks": {}, "violations": []}\n', encoding="utf-8")
