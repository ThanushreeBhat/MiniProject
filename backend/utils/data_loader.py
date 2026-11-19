import pandas as pd
from backend.config import TASK_FILE, BLOCK_FILE, TRAIN_FILE


def load_core_data():
    tasks = pd.read_csv(TASK_FILE) if TASK_FILE.exists() else pd.DataFrame()
    blocks = pd.read_csv(BLOCK_FILE) if BLOCK_FILE.exists() else pd.DataFrame()
    trains = pd.read_csv(TRAIN_FILE) if TRAIN_FILE.exists() else pd.DataFrame()
    return tasks, blocks, trains
