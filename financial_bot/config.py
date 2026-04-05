import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get BOT_TOKEN from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please create a .env file with BOT_TOKEN.")
