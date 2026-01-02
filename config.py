import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')  # Optional

# Agent settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10  # Maximum agent steps
MAX_TOKENS = 4000

# Tool settings
TOOL_IMPLEMENTATION = "anthropic"  # Options: "anthropic" or "custom"
