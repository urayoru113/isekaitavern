## Installation & Run
### Prerequisites
- Python 3.13+

### Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/urayoru113/isekaitavern
cd isekaitavern

# Install dependencies
uv sync --no-dev --frozen

# Configure environment variables
cp .env.example .env
# Edit .env and add your Discord bot token and MongoDB connection string

# Run the bot
uv run main.py
```

