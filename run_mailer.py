import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.mailer import Mailer

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else int(
        __import__("os").getenv("MAILER_INTERVAL", "15")
    )
    Mailer().run(interval=interval)
