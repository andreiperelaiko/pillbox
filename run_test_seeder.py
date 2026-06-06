import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.db_init import init_database
from src.seed_data import seed_if_empty


def main() -> None:
    interval = int(os.getenv("SEED_INTERVAL_SECONDS", "300"))
    init_database()
    print(f"Test seeder запущен, интервал {interval}с")
    while True:
        try:
            result = seed_if_empty()
            if result:
                print(f"  [seed] {result}")
            else:
                print("  [seed] данные уже есть, пропуск")
        except Exception as exc:
            print(f"  [error] {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
