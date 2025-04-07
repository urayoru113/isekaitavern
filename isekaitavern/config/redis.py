import os

import dotenv

dotenv.load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

os.environ["REDIS_OM_URL"] = REDIS_URL
