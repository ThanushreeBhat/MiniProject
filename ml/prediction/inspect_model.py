
from pathlib import Path
from backend.config import MODEL_FILE

print("MODEL PATH:")
print(MODEL_FILE)

print("\nFILE EXISTS:")
print(MODEL_FILE.exists())

if MODEL_FILE.exists():

    print("\nFILE SIZE:")
    print(MODEL_FILE.stat().st_size, "bytes")

    print("\nFIRST 100 BYTES:")
    with open(MODEL_FILE, "rb") as f:
        print(f.read(100))
