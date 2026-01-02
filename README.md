# Research Assistant - Agentic AI Application

An AI-powered research assistant that autonomously plans and executes multi-step research tasks with complete transparency. Built with server-side agentic loop control.

## Features

- **Autonomous Decision Making**: Agent decides what steps to take
- **Server-Side Control**: Full visibility into each step of the process
- **Real-Time Streaming**: Watch the agent think and work in real-time
- **Web Research**: Searches and fetches information from the web
- **Source Citations**: Provides URLs for all information used
- **Transparent Process**: See exactly how the agent reaches its conclusions

## What Makes This "Agentic"

Unlike simple chatbots that respond to a single query, this agent:

1. **Plans** its approach to research questions
2. **Decides** which tools to use and when
3. **Executes** multiple steps autonomously
4. **Adapts** based on what it finds
5. **Synthesizes** information from multiple sources
6. **Completes** when it has sufficient information

All of this happens with **server-side control**, meaning you can see, log, and control every step.

## Prerequisites

- Python 3.9+
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))
- (Optional) Brave Search API key for custom search implementation

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Edit `.env`:

```
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: For custom search (if not using Anthropic's tools)
BRAVE_API_KEY=your_brave_key_here
```

Edit `config.py` to choose tool implementation:

```python
# Use Anthropic's native tools (default)
TOOL_IMPLEMENTATION = "anthropic"

# OR use custom implementations (requires BRAVE_API_KEY)
TOOL_IMPLEMENTATION = "custom"
```

## Usage

### Start the Application

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

### Test the Agent (CLI)

```bash
python test_agent.py
```

## How It Works

### Server-Side Agentic Loop

The key innovation is that **your server controls the loop**, not Claude:

```
1. User asks question
2. Server calls Claude
3. Claude decides: search, fetch, or answer
4. If tool needed:
   - Server executes tool
   - Server adds results to conversation
   - Go to step 2
5. If no tool needed:
   - Return final answer
```

### Architecture

- **Flask App**: Handles HTTP requests and SSE streaming
- **Agent Module**: Implements server-side agentic loop
- **Tools Module**: Executes web search and fetch operations
- **Frontend**: Displays agent process in real-time

### Example Flow

```
User: "What are the latest developments in quantum computing?"

Step 1: Claude decides to search
   → Tool: web_search("quantum computing developments 2025")

Step 2: Claude analyzes results, decides to fetch article
   → Tool: web_fetch("https://quantumtech.news/...")

Step 3: Claude reads article, decides to verify with another source
   → Tool: web_search("quantum computing breakthrough verification")

Step 4: Claude has enough information
   → Returns: Synthesized answer with citations
```

## Project Structure

```
research-agent-2/
├── app.py              # Flask application with SSE
├── agent.py            # Agentic loop logic
├── tools.py            # Tool implementations
├── config.py           # Configuration
├── test_agent.py       # Testing script
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── .gitignore          # Git ignore file
├── static/
│   ├── style.css      # Styling (design system)
│   └── script.js      # Frontend with SSE
└── templates/
    └── index.html     # Main page
```

## Example Questions

- "What are the latest developments in quantum computing?"
- "Compare the renewable energy policies of the top 3 economies"
- "What is the current scientific consensus on intermittent fasting?"
- "Summarize recent breakthroughs in battery technology"
- "What are the main arguments for and against universal basic income?"

## Tool Implementations

### Option 1: Anthropic's Native Tools (Default)

- Uses Anthropic's built-in web_search and web_fetch
- Easier to set up (no additional API keys needed)
- Search and fetch handled by Anthropic

### Option 2: Custom Implementations

- Uses Brave Search API for searching
- Uses requests + BeautifulSoup for fetching
- Complete control over tool behavior
- Requires BRAVE_API_KEY

## Development

### Adding New Tools

1. Add tool definition in `agent.py`:
```python
{
    "name": "your_tool",
    "description": "What it does",
    "input_schema": {...}
}
```

2. Add execution logic in `tools.py`:
```python
def execute_your_tool(self, param):
    # Implementation
    return result
```

3. Handle tool in agent loop:
```python
elif tool_name == "your_tool":
    result = self.tool_executor.execute_your_tool(tool_input["param"])
```

### Debugging

The agent tracks all steps. Check:
- Console logs for server-side execution
- Browser console for frontend events
- `result['steps']` array for full history

## Troubleshooting

**Agent doesn't stop**: Increase MAX_ITERATIONS in config.py

**SSE not working**: Check browser console, ensure no ad blockers

**Tool execution fails**: Check API keys in .env

**Import errors**: Ensure virtual environment is activated

## Future Enhancements

- [ ] Conversation memory (multiple questions)
- [ ] Export results to PDF/Markdown
- [ ] Adjustable research depth setting
- [ ] More tools (calculator, code execution, etc.)
- [ ] Cost tracking and limits
- [ ] Save/load research sessions

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
