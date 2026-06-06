import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.scheduler import Scheduler

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else int(
        __import__("os").getenv("SCHEDULER_INTERVAL", "60")
    )
    Scheduler().run(interval=interval)
