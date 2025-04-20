import os

import dotenv

dotenv.load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis://localhost:6379/0")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb://localhost:27017")
