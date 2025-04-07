import os
from pathlib import Path

from app import create_app
from config import Config

db_dir = Path(__file__).parent / "database"
try:
    os.makedirs(db_dir, exist_ok=True)
    test_file = db_dir / "test.tmp"
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
except Exception as e:
    print(f"Database directory error: {str(e)}")
    exit(1)

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
